;;;; config.lisp

(in-package #:taiga)

;; Plain DEFCONSTANT signals when a string constant is reloaded
(alexandria:define-constant +uralex-commit+ "0ce4fc7ea8147c9b3175b786eccf87d3a1c7f7e1"
  :test #'string=)
(alexandria:define-constant +uralex-version+ "2.0" :test #'string=)
(alexandria:define-constant +uralex-doi+ "10.5281/zenodo.4777568" :test #'string=)

;; The reconstructed Proto-Uralic row (not attested variety)
(alexandria:define-constant +proto-uralic-id+ "0" :test #'string=)

(defparameter *uralic-subgroups*
  '("Saami" "Finnic" "Mordvin" "Mari" "Permic" "Ugric" "Samoyed"))

(defparameter *finno-ugric-subgroups*
  (remove "Samoyed" *uralic-subgroups* :test #'string=))

;; Gap Markers (forms.csv value)
;; Three marked gaps with DELIBERATELY DIFFERENT downstream mechanics
(alexandria:define-constant +gap-no-equivalent+ "[No equivalent]" :test #'string=)
(alexandria:define-constant +gap-form-not-found+ "[Form not found]" :test #'string=)
(alexandria:define-constant +gap-not-reconstructable+ "[Not reconstructable]" :test #'string=)
(defparameter *gap-markers* (list +gap-no-equivalent+ +gap-form-not-found+
                                  +gap-not-reconstructable+))

;;; ---------------------------------------------------------------------------
;;; Borrowing source classification

(defparameter *external-tokens*
  '("indo" "iran" "german" "baltic" "russian" "slav" "turk" "chuvash"
    "tatar" "tocharian" "yeniseian" "tungusic" "latvian" "lithuan"
    "khazar" "bulgar" "cumanian" "swedish" "norv" "european" "unknown"))

(defparameter *uralic-tokens*
  '("finnic" "finnish" "karelian" "ingrian" "izhorian" "estonian" "veps"
    "komi" "permic" "udmurt" "khanty" "ob-ugric" "ob_ugric" "mansi"
    "mordvin" "saami" "western uralic" "uralic"))

(defparameter *ii-core-labels*
  '("Indo-Iranian" "Indo-Iranian_or_Iranian" "Indo_Iranian_or_Iranian"))
