import os
'''
GENERAL INSTRUCTIONS:
- Add and remove quotations as needed, separated by commas, in each os.path.join( ... )
- Each quotation should contain the name of ONE directory, from the top to bottom-most directories  
- Enter directory names where it says <FILL> 
- Directory and file names that are already specified in quotations should be created as new folders if they do not exist already
'''


'''

REQUIRED FOR ALL OF seadoo:
- path: The directory where seadoo is located 
- repo: Where the theory files are located. Each subdirectory name should match what is found in colore/ontologies/
'''
os.environ['PROVER9'] = '/usr/local/bin'

path = "/workspaces/seadoo"
repo = os.path.join(os.path.sep, path,  'ontologies')
clif_repo = os.path.expanduser("~/colore/ontologies")

'''
USED FOR seadoo/search MODULE:
- search: Search path
- hierarchy: Directory name of the known hierarchy that is under seadoo/ontologies/. Required only for search.hashemi
- examples, counterexamples, answer_reports, translations: Create these directories under seadoo/
- alt, meta: Create these files under each hierarchy under seadoo/ontologies/<hierarchy_name>/
- db: Database details. Required only for search.modular_ontology
'''
search = os.path.join(os.path.sep, path, 'search')
hierarchy = 'orderings'
examples = os.path.join(os.path.sep, search, 'examples')
counterexamples = os.path.join(os.path.sep, search, 'counterexamples')
answer_reports = os.path.join(os.path.sep, search, 'answer_reports')
translations = os.path.join(os.path.sep, path, 'translations')
alt = os.path.join(os.path.sep, repo, hierarchy, 'alt-metatheory.owl')
meta = os.path.join(os.path.sep, repo, hierarchy, 'metatheory.owl')
db = {
    'host': 'localhost',
    'schema': 'seadoo_main',
    'user': 'seadoo',
    'pw': 'pw',
    'port': 3306,
}
'''
for issues with sql database,
1. type sudo mysql or sudo mysql -e "CREATE DATABASE IF NOT EXISTS seadoo_main;"
2. type (in mysql): 
CREATE USER 'seadoo'@'localhost' IDENTIFIED BY 'pw';

GRANT ALL PRIVILEGES ON seadoo_main.* TO 'seadoo'@'localhost';

FLUSH PRIVILEGES;



2.1 if it says "no module named config' or 'create_schema.py: no such file', then type (in bash)
PYTHONPATH=. python3 db/create_schema.py --no-insert

2.2 DROP USER IF EXISTS 'seadoo'@'localhost';

CREATE USER 'seadoo'@'localhost' IDENTIFIED BY 'pw';

GRANT ALL PRIVILEGES ON seadoo_main.* TO 'seadoo'@'localhost';

FLUSH PRIVILEGES;

3. type (in bash):
mysql -u seadoo -p < create_schema.py

4. enter password pw

--------------------------------------
to run the gui:
cd /workspaces/seadoo-main
pip install -r requirements.txt --break-system-packages
python3 nicegui/app.py

-------------------------------
if macleod doesnt import properly:
1. rm -rf ~/macleod-src
git clone https://github.com/thahmann/macleod.git ~/macleod-src
pip install -e ~/macleod-src
python3 -c "import macleod; print('OK')"

2. mkdir -p ~/macleod
cp .devcontainer/macleod_linux.conf ~/macleod/macleod_linux.conf
sed -i "s|^path:.*|path: $HOME/colore/ontologies|; s|^home:.*|home: $HOME/|" ~/macleod/macleod_linux.conf
'''

'''
USED FOR seadoo/relationship MODULE
- definitions: Create this directory under seadoo/
- create_files: Flag to generate proof files for each computation. False by default
- t1, t2: Names of two theories being checked 
'''
definitions = os.path.join(os.path.sep, path, 'definitions')
create_files = False
t1 = ''
t2 = ''


'''
USED FOR seadoo/insertion MODULE
- new_t: a new theory to be inserted into an existing hierarchy e.g., quasi_order.in
- function: 1 to insert a new theory, 2 to find the equivalent theory to new_t. 1 by default
'''
new_t = ''
function = 1
