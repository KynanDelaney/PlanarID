# Animal- / Pattern-recognition simplified

The purpose of mark-recapture photo identification methods is to take a large photographic record of unknown individuals 
and, using unique identifiers and markings, piece together which of those individuals were observed on multiple occasions.
In the course of our photography and in-person observations we may need to ascribe nicknames to these erstwhile unknown 
individuals. Naming animals is fun and useful for keeping records in line! Over time, they may even become familiar to us
but the photographic record is naive to our experience.

I mention this only to clarify that photo mark-recapture methods match _patterns_, rather than individuals. An individual 
may have been photographed on five separate occasions. Depending on the study system, that individual may have been given a 
different nickname on each of those occasions. Maybe, on each occasion, that individual was photographed three times. This
gives us 15 photographic examples, from 5 occasions, with 5 different nicknames, all of a single individual.

The language around identifying individuals in a photographic record can get confusing very quickly if we lose track of 
the hierarchy of how we collect data. An individual _contains_ several within-occasion names and maybe dozens of photographic
examples. Their unique pattern, present in each photo, is the thread by which we link up all of these photographic examples. 


<img align="center" src="readme_media/images_within_individual.svg" width="75%">

<br>

<br>

Generally, we don't know in advance whether an individual was captured multiple times. Instead we ask "have we seen this 
individual/pattern elsewhere in our photographic record?". Different individual-recognition packages approach this question
in different ways but, generally, their methods are roughly similar.

First, we can take a photographic example (or many photographic examples) of an individual in a given week and compare 
that (or those) against all other photos in our photographic record. Here, we take our blue triangle from a given occasion, 
and compare against our photographic record of of colourful polygons.

<img src="readme_media/focal_and_query_shapes.svg" width="75%">

<br>

<br>

Some algorithm compares our focal pattern against all other patterns in the photographic record and determines how well 
they match. In the graphic below thicker lines denote a better match.

<img src="readme_media/shape_pairwise_comparison.svg" width="50%">

<br>

<br>

Depending on the sophistication or bravery of the software used, the system will then either automatically assign positive
matches for the focal pattern in the photographic record (A), or sort the possible matches and present the best N matches for
the users consideration (B).

<img src="readme_media/sorted_vs_matched_shapes.svg" width="75%">

