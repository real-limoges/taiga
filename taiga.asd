(defsystem "taiga"
  :depends-on ("cl-csv" "com.inuoe.jzon" "alexandria")
  :serial t
  :components ((:module "src"
                :components ((:file "package")
                             (:file "config"))))
  :build-operation "program-op"
  :build-pathname "taiga"
  :entry-point "taiga:run-all")
