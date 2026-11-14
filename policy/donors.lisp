;;;; donors.lisp: tokens are substrings of the lowercased SourceLanguoid;
;;;; the Indo-Iranian labels match exactly.

(:external-tokens ("indo" "iran" "german" "baltic" "russian" "slav" "turk"
                          "chuvash" "tatar" "tocharian" "yeniseian" "tungusic"
                          "latvian" "lithuan" "khazar" "bulgar" "cumanian" "swedish"
                          "norv" "european" "unknown")

 :uralic-tokens ("finnic" "finnish" "karelian" "ingrian" "izhorian" "estonian"
                          "veps" "komi" "permic" "udmurt" "khanty" "ob-ugric" "ob_ugric"
                          "mansi" "mordvin" "saami" "western uralic" "uralic")

                  ;; ~4000 BP; only this layer dates the node.
 :ii-core-labels ("Indo-Iranian" "Indo-Iranian_or_Iranian" "Indo_Iranian_or_Iranian")

 :ii-later-iranian-labels ("Iranian" "West Old Turkic_or_Iranian")

 :ii-ambiguous-labels ("Indo-Iranian_or_Indo-European"))
