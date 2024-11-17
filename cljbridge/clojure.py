import subprocess
import javabridge
import json

try:
    from collections.abc import Callable  # noqa
except ImportError:
    from collections import Callable


def prepare_jvm_params(aliases=None):
    if aliases is None:
        aliases = []

    return {
        'classpath': classpath(aliases),
        'args': get_jvm_args(aliases),
    }


def init(jvm_params):
    """Initialize a vanilla clojure process using the clojure command line to output
    the classpath to use for the java vm. At the return of this function clojure is
    initialized and libpython-clj2.python's public functions will work.

    * `aliases` can be used to configure JVM arguments and class path and will be
      resolved using the local deps.edn file. """
    javabridge.start_vm(run_headless=True,
                        args=jvm_params['args'],
                        class_path=jvm_params['classpath'])
    init_clojure_runtime()
    init_libpy_embedded()


def start_repl(host, port):
    require("eeel.bootstrap")
    fn = resolve_fn("eeel.bootstrap/start-repl!")
    fn(py_dict_to_keyword_map({
        "bind": host,
        "port": port,
    }))


def init_clojure_runtime():
    """Initialize the clojure runtime.  This needs to happen at least once before
attempting to require a namespace or lookup a clojure var."""
    javabridge.static_call("clojure/lang/RT", "init", "()V")


def init_libpy_embedded():
    """Initialize libpy on a mode where it looks for symbols in the local process and
    it itself doesn't attempt to run the python intialization procedures but expects
    the python system to be previously initialized."""
    require("libpython-clj2.embedded")
    return resolve_call_fn("libpython-clj2.embedded/initialize!")


def load_file(path):
    resolve_call_fn("clojure.core/load-file", path)


def classpath(aliases, with_javabridge=True):
    """Call clojure at the command line and return the classpath in as a list of
    strings.  Clojure will pick up a local deps.edn."""
    output = subprocess.check_output(
        ['clojure'] + (['-A' + ':'.join(aliases)] if aliases else []) + ['-Spath'])
    cp = output.decode("utf-8").strip().split(':')
    if with_javabridge:
        cp += javabridge.JARS
    return cp


def get_jvm_args(aliases):
    """Call to Clojure at commandline and resolve given aliases to JVM args """
    output = subprocess.check_output([
        'clojure', '-Abootstrap', '-M', '-e',
        """(require '[clojure.tools.deps :as d]
                    '[clojure.string :as str])

           (let [basis (d/create-basis {:aliases (map keyword %s)})
                jvm-args (str/join \" \" (:jvm-opts (:argmap basis)))]
             (println jvm-args))""" % (json.dumps(aliases))])
    stripped = output.decode("utf-8").strip()
    return stripped.split(' ') if stripped else []


def py_dict_to_keyword_map(py_dict):
    hash_map = None
    keyword = resolve_fn("clojure.core/keyword")
    assoc  = resolve_fn("clojure.core/assoc")
    for k in py_dict:
        hash_map = assoc(hash_map, keyword(k), py_dict[k])
    return hash_map


def find_clj_var(fn_ns, fn_name):
    """Use the clojure runtime to find a var.  Clojure vars are placeholders in
namespaces that forward their operations to the data they point to.  This allows
someone to hold a var and but recompile a namespace to get different behavior.  They
implement both `clojure.lang.IFn` and `clojure.lang.IDeref` so they can act like a
function and you can dereference them to get to their original value."""
    return javabridge.static_call("clojure/lang/RT",
                                  "var",
                                  "(Ljava/lang/String;Ljava/lang/String;)Lclojure/lang/Var;",
                                  fn_ns,
                                  fn_name)


class CLJFn(Callable):
    """Construct a python callable from a clojure object.  This callable will forward
function calls to it's Clojure object expecting a clojure.lang.IFn interface."""
    applyTo = javabridge.make_method("applyTo", "(clojure/lang/ISeq;)Ljava/lang/Object;")
    def __init__(self, ifn_obj):
        self.o = ifn_obj

    def __call__(self, *args, **kw_args):
        if not kw_args:
            invoker = getattr(self, "invoke"+str(len(args)))
            return invoker(*args)
        else:
            raise Exception("Unable to handle kw_args for now")
        print(len(args), len(kw_args))


for i in range(20):
    opargs = ""
    for j in range(i):
        opargs += "Ljava/lang/Object;"
    setattr(CLJFn, "invoke" + str(i),
            javabridge.make_method("invoke", "(" + opargs + ")Ljava/lang/Object;" ))


def resolve_fn(namespaced_name):
    """Resolve a clojure var given a fully qualified namespace name.  The return value
    is callable.  Note that the namespace itself needs to be required first."""
    ns_name, sym_name = namespaced_name.split("/")
    return CLJFn(find_clj_var(ns_name, sym_name))


def resolve_call_fn(namespaced_fn_name, *args):
    """Resolve a function given a fully qualified namespace name and call it."""
    return resolve_fn(namespaced_fn_name)(*args)


def symbol(sym_name):
    """Create a clojure symbol from a string"""
    return javabridge.static_call("clojure/lang/Symbol", "intern",
                                  "(Ljava/lang/String;)Lclojure/lang/Symbol;", sym_name)

__REQUIRE_FN = None

def require(ns_name):
    """Require a clojure namespace.  This needs to happen before you find symbols
    in that namespace else you will be uninitialized var errors."""
    global __REQUIRE_FN
    if not __REQUIRE_FN:
        __REQUIRE_FN = resolve_fn("clojure.core/require")
    return __REQUIRE_FN(symbol(ns_name))


class GenericJavaObj:
    __str__ = javabridge.make_method("toString", "()Ljava/lang/String;")
    get_class = javabridge.make_method("getClass", "()Ljava/lang/Class;")
    __repl__ = javabridge.make_method("toString", "()Ljava/lang/String;")
    def __init__(self, jobj):
        self.o = jobj


def longCast(jobj):
    "Cast a java object to a primitive long value."
    return javabridge.static_call("clojure/lang/RT", "longCast",
                                  "(Ljava/lang/Object;)J", jobj)


def to_ptr(pyobj):
    """Create a tech.v3.datatype.ffi.Pointer java object from a python object.  This
    allows you to pass python objects directly into libpython-clj2.python-derived
    pathways (such as ->jvm).  If java is going to hold onto the python data for
    a long time and it will fall out of Python scope  object should be
    'incref-tracked' - 'libpython-clj2.python.ffi/incref-track-pyobject'."""
    return javabridge.static_call("tech/v3/datatype/ffi/Pointer", "constructNonZero",
                                  "(J)Ltech/v3/datatype/ffi/Pointer;", id(pyobj))
