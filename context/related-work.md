# Related Work

This document situates **Invariant-Anchored Intelligence (IAI)** within the existing literature on self-improving systems, optimisation under uncertainty, metric mis-specification, and safety architectures. The purpose is not to claim novelty through isolation, but to clarify precisely **where IAI aligns with, diverges from, and extends** prior work.

IAI is not a learning algorithm, a model class, or an alignment theory. It is an **architectural pattern** governing how self-improving systems relate to evaluation authority. As such, its closest antecedents span multiple fields rather than a single research lineage.

---

## 1. Recursive Self-Improvement and Intelligence Explosion

The idea that sufficiently capable systems might improve their own performance recursively is well established. Early formulations typically assume that strong self-improvement implies eventual control over objectives and evaluation.

Bostrom’s analysis of recursive self-improvement and the “intelligence explosion” frames the dominant narrative: once a system can improve its own intelligence, it may rapidly outpace human oversight and reshape its own goals [@bostrom2014]. Similar concerns are raised throughout the AI safety literature, particularly in work emerging from MIRI and related communities [@yudkowsky2008].

These accounts are valuable for identifying *risk*, but they generally treat **self-sovereignty over evaluation** as an inevitable consequence of capability growth. IAI explicitly rejects this assumption. The central claim of IAI is that **recursive improvement and evaluative sovereignty can be structurally separated**, provided evaluation authority is externalised and protected by design.

IAI therefore occupies a different point in the design space: it explores whether strong, local, domain-bounded self-improvement is possible *without* collapsing into self-defined success criteria.

---

## 2. Metric Mis-Specification, Goodhart Effects, and Reward Gaming

A large body of work documents the failure modes of optimisation when metrics are mis-specified or over-optimised.

Goodhart’s Law—“when a measure becomes a target, it ceases to be a good measure”—has been formalised and extended in modern analyses of optimisation systems [@goodhart1975; @manheim2018]. These works distinguish multiple classes of Goodhart effects, including regressional, causal, extremal, and adversarial failures.

In machine learning, reward hacking and specification gaming are well-documented phenomena, particularly in reinforcement learning systems [@amodei2016; @krakovna2020]. These failures arise even when objectives are defined with care.

IAI takes these results as **foundational constraints**, not as problems to be solved through better metrics alone. Rather than assuming invariants can be made perfect, IAI treats mis-specification as inevitable and designs for **corrigibility under mis-specification** via:

- externally governed invariants,
- explicit invariant challenge mechanisms (ICL),
- and preserved falsifiability through external evaluation authority.

---

## 3. Human-in-the-Loop and Oversight-Based Approaches

Human-in-the-loop (HITL) methods are widely used to constrain learning systems, most notably in Reinforcement Learning from Human Feedback (RLHF) [@christiano2017; @ouyang2022] and related approaches such as Constitutional AI [@bai2022].

These systems rely on human judgement to guide or constrain optimisation, typically by providing labels, preferences, or critiques. While effective in many settings, they tend to treat objectives as *fixed* and do not allow the system to meaningfully challenge or critique its own evaluation criteria.

IAI differs in two key respects:

1. **Authority separation**: Humans (or external systems) are not merely feedback providers but remain the *owners* of evaluation authority.
2. **Challenge capability**: The system is permitted—indeed encouraged—to generate structured critiques of its invariants via the Invariant Challenge Loop, while remaining prohibited from ratifying those critiques itself.

IAI can therefore be seen as complementary to oversight-based approaches, extending them into regimes where optimisation processes themselves must improve.

---

## 4. Meta-Learning, AutoML, and Learning-to-Learn

Meta-learning and AutoML systems aim to improve learning processes themselves, often by optimising architectures, hyperparameters, or training procedures [@schmidhuber1987; @finn2017; @zoph2017].

These approaches demonstrate that **learning dynamics can themselves be objects of optimisation**, a premise shared with IAI. However, meta-learning typically assumes that the evaluation metric remains fixed and internal to the optimisation process.

IAI is orthogonal to meta-learning in scope:

- Meta-learning concerns *what is optimised*.
- IAI concerns *who controls the definition and ratification of success*.

An IAI system may employ meta-learning internally, but meta-learning alone does not address the authority and corrigibility concerns central to IAI.

---

## 5. Control Theory, Cybernetics, and Systems Engineering

IAI has strong conceptual affinities with classical cybernetics and control theory, particularly the separation of system, controller, and evaluator.

Wiener’s cybernetics [@wiener1948] and Ashby’s Law of Requisite Variety [@ashby1956] emphasise that effective control requires sufficient internal complexity, but also stable feedback channels. Beer’s Viable System Model further distinguishes operational units from governance and policy layers [@beer1972].

Modern safety architectures such as Runtime Assurance (RTA) frameworks formalise similar ideas by enforcing externally verified safety constraints over adaptive systems [@schumann2019].

IAI can be understood as extending these principles to **recursive, learning-driven systems**, preserving an external evaluation boundary even as internal complexity and capability grow.

---

## 6. Formal Verification, Assurance, and Safety Envelopes

Work on formal verification, shielding, and safety envelopes aims to ensure that learning systems remain within acceptable bounds at runtime [@alshiekh2018; @schneider2020].

These approaches typically enforce hard constraints but do not address how objectives themselves evolve under optimisation pressure. IAI incorporates similar enforcement mechanisms while adding a controlled pathway—via ICL—for questioning and revising evaluation criteria without internalising authority.

---

## 7. Philosophy of Science and Falsifiability (Optional Context)

The Invariant Challenge Loop bears resemblance to ideas in the philosophy of science concerning theory revision under constraint.

Popper’s emphasis on falsifiability [@popper1959] and Lakatos’ notion of research programmes [@lakatos1978] both stress that progress requires the ability to challenge assumptions while preserving an external standard of evaluation.

IAI operationalises this insight in an engineering context: systems may propose revisions to their evaluative framework, but falsification and ratification remain external.

---

## 8. Summary of Positioning

Across these literatures, IAI is distinguished by a single architectural commitment:

> **Recursive self-improvement is permitted; evaluative sovereignty is not.**

Rather than eliminating mis-specification, Goodhart effects, or optimisation risk, IAI treats them as structural facts and designs systems that remain corrigible, auditable, and falsifiable in their presence.

---

## Bibliography (BibTeX)

```bibtex
@book{bostrom2014,
  title={Superintelligence: Paths, Dangers, Strategies},
  author={Bostrom, Nick},
  year={2014},
  publisher={Oxford University Press}
}

@article{yudkowsky2008,
  title={Artificial Intelligence as a Positive and Negative Factor in Global Risk},
  author={Yudkowsky, Eliezer},
  journal={Global Catastrophic Risks},
  year={2008}
}

@article{goodhart1975,
  title={Problems of Monetary Management: The UK Experience},
  author={Goodhart, Charles},
  journal={Papers in Monetary Economics},
  year={1975}
}

@article{manheim2018,
  title={Categorizing Variants of Goodhart's Law},
  author={Manheim, David and Garrabrant, Scott},
  year={2018},
  journal={arXiv preprint arXiv:1803.04585}
}

@article{amodei2016,
  title={Concrete Problems in AI Safety},
  author={Amodei, Dario et al.},
  journal={arXiv preprint arXiv:1606.06565},
  year={2016}
}

@article{krakovna2020,
  title={Specification Gaming: The Flip Side of AI Ingenuity},
  author={Krakovna, Victoria et al.},
  journal={DeepMind Blog},
  year={2020}
}

@article{christiano2017,
  title={Deep Reinforcement Learning from Human Preferences},
  author={Christiano, Paul et al.},
  journal={Advances in Neural Information Processing Systems},
  year={2017}
}

@article{ouyang2022,
  title={Training Language Models to Follow Instructions with Human Feedback},
  author={Ouyang, Long et al.},
  journal={arXiv preprint arXiv:2203.02155},
  year={2022}
}

@article{bai2022,
  title={Constitutional AI: Harmlessness from AI Feedback},
  author={Bai, Yuntao et al.},
  journal={arXiv preprint arXiv:2212.08073},
  year={2022}
}

@article{schmidhuber1987,
  title={Evolutionary Principles in Self-Referential Learning},
  author={Schmidhuber, Jürgen},
  year={1987}
}

@article{finn2017,
  title={Model-Agnostic Meta-Learning for Fast Adaptation of Deep Networks},
  author={Finn, Chelsea et al.},
  journal={Proceedings of ICML},
  year={2017}
}

@article{zoph2017,
  title={Neural Architecture Search with Reinforcement Learning},
  author={Zoph, Barret and Le, Quoc},
  journal={Proceedings of ICLR},
  year={2017}
}

@book{wiener1948,
  title={Cybernetics},
  author={Wiener, Norbert},
  year={1948},
  publisher={MIT Press}
}

@book{ashby1956,
  title={An Introduction to Cybernetics},
  author={Ashby, W. Ross},
  year={1956},
  publisher={Chapman & Hall}
}

@book{beer1972,
  title={Brain of the Firm},
  author={Beer, Stafford},
  year={1972},
  publisher={Allen Lane}
}

@article{schumann2019,
  title={Toward Real-Time Assurance of Learning-Enabled Autonomous Systems},
  author={Schumann, Johann et al.},
  journal={NASA Technical Reports},
  year={2019}
}

@article{alshiekh2018,
  title={Safe Reinforcement Learning via Shielding},
  author={Alshiekh, Mohammad et al.},
  journal={AAAI},
  year={2018}
}

@book{popper1959,
  title={The Logic of Scientific Discovery},
  author={Popper, Karl},
  year={1959},
  publisher={Routledge}
}

@book{lakatos1978,
  title={The Methodology of Scientific Research Programmes},
  author={Lakatos, Imre},
  year={1978},
  publisher={Cambridge University Press}
}
