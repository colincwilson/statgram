# statgram

Static Grammar is an approach to phonology and other parts of language that adopts much of Harmonic Grammar (Legendre et al., 1990) and Optimality Theory (Prince & Smolensky 1993/2004), with one key difference: well-formedness is determined by a simple threshold nonlinearity to each part of a given structure, rather than by optimization over alternative structures.

---

Static Harmonic Grammar (HGStat)

* **Representation**. Each representation permitted by **Gen** is a *relational structure* consisting of a finite non-empty set of nodes and relations on those nodes (e.g., unary relations that label the nodes as segments, valued features, or prosodic units; binary relations of precedence, association, and constituency).
&nbsp;
  
* **Evaluation**. A constraint $c_k$ in **Con** evaluates each node $n$ within its structure $M$, assigning the node a *signed unit mark* or zero: $c_k(n; M) \in \{-1, 0, +1\}$. Two constraints conflict at a node if they assign it marks of opposite sign.  
&nbsp;

* **Harmony**. Given constraint weights $\mathbf{w}$, the harmony of a node is determined by summing its weighted marks and applying an upper threshold of zero:  
$$\begin{aligned}h(n; M)  & = \min(0, \sum_{k} w_k, c_k(n; M))\\
& = {\min}_0 \sum_{k} w_k c_k(n;M)\end{aligned}$$ and the harmony of a structure is the sum of the harmonies of its nodes:
$$\begin{aligned}h(M) & = \sum_{n \in M} h(n; M)\end{aligned}$$
* **Well-formedness**. A node is well-formed iff its harmony is non-negative (i.e., zero). A structure  is well-formed iff all of its nodes are &mdash; equivalently, when its harmony is zero.

Static OT (OTStat) is defined in the same way, except that node harmony is determined by a strict-domination ranking.

* **Harmony**. Given constraint ranking $\mathbf{r}$, the harmony of a node is:
$$h(n; M) = \begin{cases}
        \phantom{-}0 & \begin{array}{l}\text{if every constraint that assigns $-1$ to $n$ is dominated}\\
        \text{by some constraint that assigns $+1$ to $n$}\end{array}\\
        -1 & \text{otherwise}
    \end{cases}$$

---

Because harmony and well-formedness are defined with elementary functions, static grammars have no logical expressivity or computational complexity beyond that needed to define the space of possible structures (**Gen**) and state the constraints (**Con**).

* If **Gen** and **Con** can be formalized in a particular logic (e.g., predicate logic), then an entire weighted/ranked grammar corresponds to a single conjunctive normal form statement in the same logic and the well-formed structures are the models of that statement.

* If **Gen** and **Con** can be implemented with a single finite-state machine, in which states encode local or tier-based contexts and nodes live on arcs, then a particular weighted/ranked grammar is derived by pruning some of the arcs (those representing nodes with negative harmony). The result of pruning is a finite-state machine that represents a regular language or rational relation. Each path through the machine specifies a well-formed structure.

---

Static Grammar was directly inspired by Smolensky (1993) and Hale & Smolensky (2001, 2006), which use local accumulation of positive and negative harmony contributions to formalize context-free grammars (see also Smolensky 2012). The application of a threshold non-linearity  subsequent to weighted summation, while not part of those proposals, is uniquitous in both early connectionist model (e.g., Rosenblatt 1958) and contemporary deep neural networks. In particular, the ${\min}_0$ ("minnow") non-linearity is identical to the highly successful $ReLU$ activation function (Nair & Hinton 2010) with a change of sign, ${\min}_0(x) = - ReLU(-x)$.