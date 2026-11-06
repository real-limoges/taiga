;;;; config.lisp

(in-package #:taiga)

;;; Pinned data source.
;;; A string is not EQL to itself across loads, so plain DEFCONSTANT signals on
;;; reload; DEFINE-CONSTANT compares with STRING= instead.

(alexandria:define-constant +uralex-commit+ "0ce4fc7ea8147c9b3175b786eccf87d3a1c7f7e1"
  :test #'string=)
(alexandria:define-constant +uralex-version+ "2.0" :test #'string=)
(alexandria:define-constant +uralex-doi+ "10.5281/zenodo.4777568" :test #'string=)

;;; Taxa.

;; The reconstructed Proto-Uralic row. It is a reconstruction, not an attested
;; variety: it never decides the loan status of a cognate set, and downstream it
;; is flagged so it can be kept as a tip or treated as an ancestral constraint.
(alexandria:define-constant +proto-uralic-id+ "0" :test #'string=)

;; The traditional Uralic subgroups present in the sampled data.
(defparameter *uralic-subgroups*
  '("Saami" "Finnic" "Mordvin" "Mari" "Permic" "Ugric" "Samoyed"))

;; Every subgroup except Samoyed, the first split in the standard tree.
;; The calibration stage uses it to define the Finno-Ugric crown node.
(defparameter *finno-ugric-subgroups*
  (remove "Samoyed" *uralic-subgroups* :test #'string=))
