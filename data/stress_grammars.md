### Stress grammars  
02/14/2020

* Represent prosodic constituency structure with nltk.tree

```{python, eval=FALSE}
from nltk.tree import Tree
string1 = '(PrWd (Ft (HdSyll x) (Syll x)) (HdFt (HdSyll x) (Syll x)))'
tree1 = Tree.fromstring(string1)
tree1.pprint() # or tree1.pformat()
tree1.pretty_print() # ascii art

for s in tree1.subtrees():
    print (type(s), s)

len(tree1) # number of constituents of root
tree1[0].label() # label of first constituent of root
tree1[1].label() # label of second constituent of root
```

* Associate a dictionary or vector of marks with each node (subtree)

```{python, eval=FALSE}
tree1.marks = dict()
tree1.marks['C1'] = +1.0
tree1.marks['C2'] = -1.0
```

* Prosody CFG (Gen)

```{python, eval=FALSE}
from nltk import CFG

# Expansions of PrWd
rules = []
rules_old = ['']
for i in range(2):
    rules_new = []
    for y in ['HdFt', 'Ft', 'Syll']:
        rules_new = [x+' '+y for x in rules_old]
    rules += rules_new
    rules_old = rules_new

rules = ['PrWd -> '+ x for x in rules]
print(rules)

grammar = CFG.fromstring("""
    PrWd -> Ft | HdFt | Syll | 
""")
```