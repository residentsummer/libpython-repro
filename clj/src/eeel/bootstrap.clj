(ns eeel.bootstrap
  (:require [nrepl.cmdline :as cmdline]
            [nrepl.server :as server]
            [clojure.tools.logging :as log]))


(defonce ^:private repl-server* (atom nil))

(defn start-repl!
  ([options]
   (when-not @repl-server*
     (let [options (cmdline/server-opts
                    (merge {:middleware '[cider.nrepl/cider-middleware]}
                           options))
           server (cmdline/start-server options)
           _ (reset! repl-server* server)]
       (cmdline/ack-server server options)
       ;; (cmdline/save-port-file server options)
       (log/info (cmdline/server-started-message server options))))
   (:port @repl-server*))
  ([] (start-repl! nil)))

(defn stop-repl!
  "If an existing repl has been started, stop it.  This returns control to the
  thread that called `start-repl!`."
  []
  (swap! repl-server*
         (fn [server]
           (when server
             (server/stop-server server)
             nil))))
