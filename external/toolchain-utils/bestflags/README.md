# bestflags

There is a vast set of compiler flags that can be used to build Chrome for
ChromeOS. This option space has not been explored before. This directory
provides an infrastructure to build Chrome with certain flag combinations, test
it, gather results and prepare a fresh batch of flags to repeat the process. The
infrastructure supports plug-in modules that implement algorithms for searching
in the N-Dimensional space of compiler flag combinations.

Currently, three different algorithms are built, namely genetic algorithm, hill
climbing and negative flag iterative elimination. The module `testing_batch.py`
contains the testing of these algorithms.

To run the script, type in `python testing_batch.py`.

For further information about the project, please refer to the design document
at:

https://docs.google.com/a/google.com/document/d/19iE9rhszTWjISBpKJ3qK8uBCoUjs0o4etWDRkyEeUOw/

There is also a presentation slide available at:

https://docs.google.com/a/google.com/presentation/d/13rS9jALXffbP48YsF0-bsqovrVBfgzEud4e-XpavOdA/edit#slide=id.gf880fcd4_180
