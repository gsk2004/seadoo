# Semi-Automated Design of Ontologies

Used in conjunction with logical and mathematical theories (i.e., ontologies) found 
in the [Common Logic Ontology Repository (COLORE)](https://github.com/gruninger/colore). 
For further research and development, see the [SEADOO wiki](https://github.com/acchow/seadoo/wiki). 

## Environment Setup

### Prerequisites

VS Code with the Dev Containers extension, or a GitHub Codespace

### Setup
1. Open this repo in VS Code → "Reopen in Container" (or launch a Codespace). This runs .devcontainer/post_create.sh automatically, which:
- Clones COLORE into ~/colore and macleod into ~/macleod-src
- Builds Prover9, Mace4, interpformat, and prooftrans from source
- Starts MariaDB
- Installs macleod and this repo's own dependencies

2. Confirm the build actually completed cleanly:
```
bash
   which prover9 mace4 interpformat prooftrans
```

All four should resolve. If any are missing, fix that before continuing.

3. Set up the database:
```
bash
   sudo mysql -e "CREATE DATABASE IF NOT EXISTS seadoo_main;"
   sudo mysql -e "GRANT ALL PRIVILEGES ON seadoo_main.* TO 'seadoo'@'localhost'; FLUSH PRIVILEGES;"
   cd /workspaces/seadoo   
   PYTHONPATH=. python3 db/create_schema.py --no-insert
```


## Running the pipeline
- Sync a single hierarchy (recommended first - the full COLORE corpus is ~190 hierarchies and can take a very long time to process completely):
```
python3 sync.py --clif-root ~/colore/ontologies/orderings --manifest ~/colore/orderings_manifest.json
```
- Sync everything (it can take hours):
```
nohup python3 sync.py --clif-root ~/colore/ontologies --manifest ~/colore/sync_manifest.json > sync_full.log 2>&1 &
disown
tail -f sync_full.log   # to watch progress
```
- Populate the MySQL metadata table (hierarchy names, root theories):
```
python3 populate_hierarchies.py --colore-ontologies ~/colore/ontologies
```

## Querying a hierarchy
- Can run search.hashemi and search.modular_ontology from here on.
```
import config
config.hierarchy = 'orderings'
from search.hashemi import hashemi
print(''.join(hashemi('orderings', report=True)))
```
This needs example models (and optionally counterexample models) placed in search/examples/ and search/counterexamples/ as .in files

- Automatically generate a Mace4-verified counterexample for a given example
```
python3 search/generate_counterexample.py \
    --hier orderings \
    --example search/examples/your_example.in \
    --out search/counterexamples/generated_counter.in
```

### **search/hashemi**
Implementation of the Hashemi procedure. Constructs the closest matching theory to 
models provided by the user (consistent with all examples and inconsistent with all counterexamples)
using existing axioms from a *chsain decomposition of theories. 
Generates additional models for user to classify as intended or unintended. Final answer containing
best matching axioms are generated in an answer report (.txt file). 

*chain decomposition: hierarchy of theories represented as linear chains, where one path from root to
leaf theory is equivalent to one chain

#### Files Required
1. Model files in Mace4 'cooked' format, classified as examples and counterexamples (place examples
and counterexamples in separate directories)
2. Definition files for non-primitive relations used in 
the theories (use the relation signature as the file name)
3. Translation definition files that map relations in the models to 
relations in the theories (use the relation name in the models as the file name)

Important notes: 
* name all files with the suffix ".in"
* all axioms must be written in Prover9 syntax
* write all comments with a period at the end

### **search/modular_ontology**
Extension of the Hashemi procedure to generate modular ontologies. Checks for consistent nondecomposable theories by root theory comparison and whether residue axioms from weakly reducible hierarchies are required to generate an ontology bottom-up. The same setup files as `search.hashemi` are required. 

#### Run modular ontology generation procedure from /seadoo
```
mv ~/seadoo/config_template.py ~/seadoo/config.py       //Follow instructions for setup in config.py
python3 -m db.create_schema
python3 -m search.modular_ontology.py
```
</br>

## 

## **p9_tools**
Additional packages used for [hashemi](#hashemi). Can also be used independently as tools
for theories in Prover9 syntax. The [parse](https://github.com/acchow/seadoo/tree/master/p9_tools/parse) 
module is required for all other functionality. 

### **p9_tools/relationship**
Checks for consistency and finds the relationship between two theories. Prover9 is set to terminate after 30 seconds by default if a proof cannot be found.  Mace4 is set to terminate after searching for 10 models, or 30 seconds (whichever comes sooner). 

There are 6 different outcomes:
1. equivalent
2. one theory entails the other 
3. independent 
4. consistent 
5. inconsistent
6. inconclusive 

#### Run relationship from seadoo/
```
mv ~/seadoo/config_template.py ~/seadoo/config.py    //Follow instructions for setup in config.py
python3 -m p9_tools.relationship.relationship
```
<br/>

### **p9_tools/insertion**
There are 3 use cases for this package: 
1. Insert a theory into an existing chain decomposition (.csv file)
2. Search for an equivalent theory in an existing chain decomposition (.csv file)
3. Construct a new chain decomposition

### Use Case 1 and 2
#### Run insertion from seadoo/
```
mv ~/seadoo/config_template.py ~/seadoo/config.py    //Follow instructions for setup in config.py
python3 -m p9_tools.insertion.insertion
```

### Use Case 3
#### Run construct from seadoo/
```
mv ~/seadoo/config_template.py ~/seadoo/config.py    //Follow instructions for setup in config.py
touch <name_of_chain_decomp>.csv                     //Open this file and add a 0 as the first entry
python3 -m p9_tools.insertion.construct
```
<br><br/>
