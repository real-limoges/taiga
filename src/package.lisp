;;;; package.lisp

(defpackage #:taiga
  (:use #:cl)
  (:export
   ;; config: pinned data source
   #:+uralex-commit+
   #:+uralex-version+
   #:+uralex-doi+
   ;; config: taxa
   #:+proto-uralic-id+
   #:*uralic-subgroups*
   #:*finno-ugric-subgroups*
   ;; cli: the program-op entry point named in taiga.asd (not yet defined)
   #:run-all))
