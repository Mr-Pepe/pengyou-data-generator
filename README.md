This repository handles the parsing of several data sources and merges them together in one SQLite3 database to be used be the [pengyou app](https://github.com/Mr-Pepe/pengyou).

In order to build the database using all resources, run the run_all.py file. 

Sources are obtained from the following links:

#### [CC-CEDICT Open Source Dictionary](https://www.mdbg.net/chinese/dictionary?page=cc-cedict)
The dictionary is licensed under the  [Creative Commons Attribution-ShareAlike 4.0 International License](https://creativecommons.org/licenses/by-sa/4.0/).


#### [Stroke Order Data](https://github.com/chanind/hanzi-writer-data)

Download all.json from [here](https://github.com/chanind/hanzi-writer-data/tree/master/data).

This data comes from the Make Me A Hanzi project, which extracted the data from fonts by Arphic Technology, a Taiwanese font forge that released their work under a permissive license in 1999. You can redistribute and/or modify this data under the terms of the Arphic Public License as published by Arphic Technology Co., Ltd. A copy of this license can be found in [here](license/ARPHICPL.txt).


#### [Character Decomposition Data](https://github.com/amake/cjk-decomp)

The data is shipped with the app but unused at the moment. 
Licensed under several licenses, e.g., [Creative Commons BY-SA 3.0](https://creativecommons.org/licenses/by-sa/3.0/legalcode).


#### [Character Frequency Data](https://github.com/czielinski/hanzifreq)

Character frequency data calculated on the Chinese Wikipedia


#### [Traditional to Simplified Transformation](https://github.com/BYVoid/OpenCC/)

Licensed under an [Apache License 2.0](https://apache.org/licenses/LICENSE-2.0).


#### [Unihan](https://unicode.org/charts/unihan.html)

Used when CEDICT doesn't have a definition.
