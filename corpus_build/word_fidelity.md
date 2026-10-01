# Word-level fidelity, one legacy-decode substitution tolerated

An OCR word counts as present if the page text layer holds it or any word within one edit, computed exactly with a single-deletion index. The tolerance is set to the measured failure mode of the context-free decoder (`व्यथा` -> `िबथा`, `बारूद` -> `बा:द`); words under 3 characters are excluded because particles dominate with noise.

Thresholds: worst page >= 0.88 `verified`, 0.8-0.88 `review`, below 0.8 `page-failure`.

| chapter | lang | pages | scored | worst | mean | below | warn | verdict |
|---|---|---|---|---|---|---|---|---|
| aejm1-ch13 | en-IN | 11 | 9 | 0.9574 | 0.9878 | 0 | 0 | verified |
| fegp1-ch10 | en-IN | 56 | 43 | 0.9326 | 0.9984 | 0 | 0 | verified |
| fepr1-ch05 | en-IN | 34 | 34 | 0.9375 | 0.9953 | 0 | 0 | verified |
| gecu1-ch12 | en-IN | 20 | 19 | 0.9032 | 0.9782 | 0 | 0 | verified |
| gegp1-ch04 | en-IN | 41 | 41 | 0.9861 | 0.9992 | 0 | 0 | verified |
| gepr1-ch02 | en-IN | 48 | 48 | 0.9636 | 0.9957 | 0 | 0 | verified |
| jhkr1-ch01 | hi-IN | 9 | 8 | 0.9714 | 0.9884 | 0 | 0 | verified |
| jhkr1-ch02 | hi-IN | 14 | 14 | 0.9385 | 0.9693 | 0 | 0 | verified |
| jhkr1-ch03 | hi-IN | 5 | 5 | 0.8947 | 0.9377 | 0 | 0 | verified |
| jhks1-ch01 | hi-IN | 9 | 8 | 0.9412 | 0.973 | 0 | 0 | verified |
| jhks1-ch02 | hi-IN | 7 | 7 | 0.9333 | 0.9504 | 0 | 0 | verified |
| jhks1-ch03 | hi-IN | 5 | 5 | 0.9211 | 0.9702 | 0 | 0 | verified |
| jhks1-ch04 | hi-IN | 6 | 5 | 0.9412 | 0.9734 | 0 | 0 | verified |
| jhks1-ch05 | hi-IN | 7 | 7 | 0.9143 | 0.9618 | 0 | 0 | verified |
| jhks1-ch06 | hi-IN | 8 | 7 | 0.9355 | 0.9617 | 0 | 0 | verified |
| jhks1-ch07 | hi-IN | 9 | 9 | 0.9268 | 0.9587 | 0 | 0 | verified |
| jhks1-ch08 | hi-IN | 9 | 9 | 0.9263 | 0.9731 | 0 | 0 | verified |
| jhks1-ch09 | hi-IN | 6 | 6 | 0.9756 | 0.9872 | 0 | 0 | verified |
| jhks1-ch10 | hi-IN | 12 | 12 | 0.9635 | 0.9781 | 0 | 0 | verified |
| jhks1-ch11 | hi-IN | 12 | 12 | 0.9114 | 0.9726 | 0 | 0 | verified |
| jhks1-ch12 | hi-IN | 8 | 7 | 0.9388 | 0.97 | 0 | 0 | verified |
| jhsp1-ch01 | hi-IN | 7 | 5 | 0.9286 | 0.9452 | 0 | 0 | verified |
| jhsp1-ch02 | hi-IN | 5 | 5 | 0.913 | 0.9572 | 0 | 0 | verified |
| jhsp1-ch03 | hi-IN | 7 | 6 | 0.9107 | 0.9573 | 0 | 0 | verified |
| jhsp1-ch04 | hi-IN | 6 | 6 | 0.9231 | 0.9513 | 0 | 0 | verified |
| jhsp1-ch05 | hi-IN | 5 | 5 | 0.9385 | 0.9683 | 0 | 0 | verified |
| jhsp1-ch06 | hi-IN | 5 | 5 | 0.9355 | 0.9633 | 0 | 0 | verified |
| jhsp1-ch07 | hi-IN | 5 | 5 | 0.9385 | 0.9516 | 0 | 0 | verified |
| jhsp1-ch08 | hi-IN | 17 | 16 | 0.9643 | 0.9862 | 0 | 0 | verified |
| jhsp1-ch09 | hi-IN | 9 | 9 | 0.9079 | 0.9527 | 0 | 0 | verified |
| jhsp1-ch10 | hi-IN | 12 | 12 | 0.8909 | 0.9617 | 0 | 0 | verified |
| jhsp1-ch11 | hi-IN | 10 | 10 | 0.9298 | 0.9606 | 0 | 0 | verified |
| jhsp1-ch12 | hi-IN | 8 | 8 | 0.9255 | 0.9724 | 0 | 0 | verified |
| jhsp1-ch13 | hi-IN | 10 | 10 | 0.9403 | 0.9624 | 0 | 0 | verified |
| jhsp1-ch14 | hi-IN | 10 | 10 | 0.9423 | 0.9852 | 0 | 0 | verified |
| jhsy1-ch01 | hi-IN | 19 | 18 | 0.9569 | 0.9852 | 0 | 0 | verified |
| jhsy1-ch02 | hi-IN | 12 | 11 | 0.9385 | 0.9738 | 0 | 0 | verified |
| jhsy1-ch03 | hi-IN | 13 | 11 | 0.9138 | 0.9758 | 0 | 0 | verified |

Tally: {'verified': 38}
