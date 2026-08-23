;;;; stage0-config.lisp


;; pinned data source
(defconstant *uralex-commit* "0ce4fc7ea8147c9b3175b786eccf87d3a1c7f7e1")
(defconstant *uralex-version* "2.0")
(defconstant *uralex-doi* "10.5281/zenodo.4777568")

(defconstant *proto-uralic-id* "0")

(defparameter uralic-subgroups
  '("Saami" "Finnic" "Mordvin" "Mari" "Permic" "Ugric" "Samoyed"))

(defparameter finnno-ugric-subgroups
  (- *uralic-sugbroups* "Samoyed"))
