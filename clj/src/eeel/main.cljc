(ns eeel.main
  (:require
   [libpython-clj2.python :as py]
   [libpython-clj2.require :refer [require-python]]
   [libpython-clj2.python.ffi :refer [with-gil incref-track-pyobject]]
   ;;
   ))

(require-python '[core.app :as pyapp])
(require-python '[core.interop :as pyinterop])

(defonce taps (atom []))

(defn save-to-tap [obj]
  (swap! taps conj obj))

(defn save-to-tap-with-incref [obj]
  (let [tracked (with-gil (incref-track-pyobject obj))]
    (swap! taps conj tracked)))

(defn save-to-tap-with-borrow [obj]
  (pyinterop/borrow obj)
  (swap! taps conj obj))

(defn -main [& args]
  (println "clojure -main called")
  ;; This method leads to a crash
  (pyapp/set_tap save-to-tap)
  ;; This one too
  ;; (pyapp/set_tap save-to-tap-with-incref)
  ;; This hack does not
  ;; (pyapp/set_tap save-to-tap-with-borrow)
  (loop [_ 1]
    (pyapp/save_something)
    (println "taps:" @taps)
    (Thread/sleep 1000)
    (recur 1)))
