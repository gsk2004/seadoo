# Semi-Automated Design of Ontologies

Used in conjunction with logical and mathematical theories (i.e., ontologies) found 
in the [Common Logic Ontology Repository (COLORE)](https://github.com/gruninger/colore). 
For further research and development, see the [SEADOO wiki](https://github.com/acchow/seadoo/wiki). 

## 1. Environment Setup
```
python3 -m venv venv                    //Create virtual environment
source venv/bin/activate                //Activate
pip install -r requirements.txt         //Install requirements
```
#### 1.1 Install MySQL
Install MySQL https://dev.mysql.com/downloads/installer/ for the database to be used later. During setup, create a database called seadoo and note your root password

#### 1.2 Set up config file
Run
```
mv ~/seadoo/config_template.py ~/seadoo/config.py       //Follow instructions for setup in config.py
```
<br/>

## 2. Install theorem prover
[Prover9/Mace4 (LADR)](https://www.cs.unm.edu/~mccune/prover9/download/) <br />
Then, add the following line to your run command config file (i.e., `~/.zshrc` (Mac), `~/.bashrc` (Linux))
```
export PATH="<file_location_of_installed_prover>/LADR-2009-11A/bin:$PATH"
```
<br/>

## 3. **search/hashemi**
Implementation of the Hashemi procedure. Constructs the closest matching theory to 
models provided by the user (consistent with all examples and inconsistent with all counterexamples)
using existing axioms from a *chsain decomposition of theories. 
Generates additional models for user to classify as intended or unintended. Final answer containing
best matching axioms are generated in an answer report (.txt file). 

*chain decomposition: hierarchy of theories represented as linear chains, where one path from root to
leaf theory is equivalent to one chain

#### 3.1 Files Required
1. Chain decomposition in a .csv file ([learn how to construct a new one](#insertion-and-hierarchy-construction))
2. Theory files containing respective axioms (in Prover9 syntax) for each theory listed in the 
chain decomposition
3. Model files in Mace4 'cooked' format, classified as examples and counterexamples (place examples
and counterexamples in separate directories)
4. Definition files for non-primitive relations used in 
the theories (use the relation signature as the file name)
5. Translation definition files that map relations in the models to 
relations in the theories (use the relation name in the models as the file name)

Important notes: 
* for #2-5, name all files with the suffix ".in"
* all axioms must be written in Prover9 syntax
* write all comments with a period at the end

#### 3.2 Run hashemi procedure from /seadoo
```
python3 -m search.hashemi
```
<br/>

## 4. **search/modular_ontology**
Extension of the Hashemi procedure to generate modular ontologies. Checks for consistent nondecomposable theories by root theory comparison and whether residue axioms from weakly reducible hierarchies are required to generate an ontology bottom-up. The same setup files as `search.hashemi` are required. 

An SQL database should be set up as well, with credentials specified in the config file. The queries to create the schema and insert values are under `db/`. Additional entries may be required for future development, as it currently only contains information about hierarchies used in preliminary testing data, which are: the `orderings`, `graphs`, `subposet`, `subgraph`, and `mereograph` hierarchies. The `nondecomp_hierarchies` column entries must be listed in alphabetical order. 

#### 4.1 Run modular ontology generation procedure from /seadoo
```
mv ~/seadoo/config_template.py ~/seadoo/config.py       //Follow instructions for setup in config.py
python3 -m db.create_schema
python3 -m search.modular_ontology.py
```
</br>

## 5. Running modular ontology and hashemi 

After running search.modular_ontology in the terminal, the code will call search.hashemi which will then ask to confirm if the upper and lower bound theories are an example for the relation in a particular bracket.
A general rule for understanding:
1. ub (upper bound) means that the model satisfies the first theory but violates the second theory (if it asks ub_model_quasiorder_partial_ordering.in, it means the example satisfies quasiorder but violate partial_ordering if said yes)
2. lb (lower bound) means that the model satisfies the first theory but not yet the second theory.

<br>

## 6. **p9_tools**
Additional packages used for [hashemi](#hashemi). Can also be used independently as tools
for theories in Prover9 syntax. The [parse](https://github.com/acchow/seadoo/tree/master/p9_tools/parse) 
module is required for all other functionality. 

## 6.1 **p9_tools/relationship**
Checks for consistency and finds the relationship between two theories. Prover9 is set to terminate after 30 seconds by default if a proof cannot be found.  Mace4 is set to terminate after searching for 10 models, or 30 seconds (whichever comes sooner). 

There are 6 different outcomes:
1. equivalent
2. one theory entails the other 
3. independent 
4. consistent 
5. inconsistent
6. inconclusive 

#### 6.1.1 Run relationship from seadoo/
```
mv ~/seadoo/config_template.py ~/seadoo/config.py    //Follow instructions for setup in config.py
python3 -m p9_tools.relationship.relationship
```
<br/>

## 6.2 **p9_tools/insertion**
There are 3 use cases for this package: 
1. Insert a theory into an existing chain decomposition (.csv file)
2. Search for an equivalent theory in an existing chain decomposition (.csv file)
3. Construct a new chain decomposition

### 6.2.1 Use Case 1 and 2
#### Run insertion from seadoo/
```
mv ~/seadoo/config_template.py ~/seadoo/config.py    //Follow instructions for setup in config.py
python3 -m p9_tools.insertion.insertion
```

### 6.2.2 Use Case 3
#### Run construct from seadoo/
```
mv ~/seadoo/config_template.py ~/seadoo/config.py    //Follow instructions for setup in config.py
touch <name_of_chain_decomp>.csv                     //Open this file and add a 0 as the first entry
python3 -m p9_tools.insertion.construct
```
<br><br/>
