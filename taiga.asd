(defsystem "taiga"
  :depends-on ("cl-csv" "com.inuoe.jzon" "alexandria")
  :serial t
  :components ((:module "src"
                :components ((:file "package")
                             (:file "config")
                             (:file "io"))))
  :build-operation "program-op"
  :build-pathname "taiga"
  :entry-point "taiga:run-all")
