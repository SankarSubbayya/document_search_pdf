# Visual Comparison of Chunking Strategies

This document provides visual representations of how each chunking strategy processes documents differently.

---

## 📄 Example Document

Consider this sample document:

```markdown
# Machine Learning Fundamentals

Machine learning is a subset of artificial intelligence that enables 
systems to learn from data without being explicitly programmed.

## Supervised Learning

Supervised learning uses labeled data to train models. The algorithm 
learns from examples with known outcomes and makes predictions on new data.

### Classification

Classification predicts discrete categories. Common algorithms include 
decision trees, random forests, and neural networks.

### Regression

Regression predicts continuous values. Popular methods are linear 
regression, polynomial regression, and ridge regression.

## Unsupervised Learning

Unsupervised learning finds patterns in unlabeled data without predefined 
categories or targets.
```

---

## 1️⃣ Traditional Token Chunking (Baseline)

**How it works**: Splits text every N tokens regardless of structure.

```
┌────────────────────────────────────┐
│ Machine learning is a subset of    │ Chunk 1 (arbitrary split)
│ artificial intelligence that       │
│ enables systems to learn from      │
├────────────────────────────────────┤
│ data without being explicitly      │ Chunk 2 (mid-sentence)
│ programmed. Supervised learning    │
│ uses labeled data to train models. │
├────────────────────────────────────┤
│ The algorithm learns from examples │ Chunk 3 (no context)
│ with known outcomes and makes      │
│ predictions on new data.           │
└────────────────────────────────────┘
```

**Issues**:
- ❌ Splits mid-sentence
- ❌ Loses semantic meaning
- ❌ No structure awareness
- ❌ Context lost at boundaries

---

## 2️⃣ Markup Chunking (Structure-Aware)

**How it works**: Chunks based on document structure (headings, sections).

```
┌─────────────────────────────────────────────┐
│ # Machine Learning Fundamentals            │ Chunk 1
│                                             │ Hierarchy: ["ML Fundamentals"]
│ Machine learning is a subset of artificial │
│ intelligence that enables systems...       │
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ## Supervised Learning                      │ Chunk 2
│                                             │ Hierarchy: ["ML Fundamentals",
│ Supervised learning uses labeled data...   │              "Supervised Learning"]
└─────────────────────────────────────────────┘

┌─────────────────────────────────────────────┐
│ ### Classification                          │ Chunk 3
│                                             │ Hierarchy: ["ML Fundamentals",
│ Classification predicts discrete...         │              "Supervised Learning",
└─────────────────────────────────────────────┘              "Classification"]

┌─────────────────────────────────────────────┐
│ ### Regression                              │ Chunk 4
│                                             │ Hierarchy: ["ML Fundamentals",
│ Regression predicts continuous...          │              "Supervised Learning",
└─────────────────────────────────────────────┘              "Regression"]

┌─────────────────────────────────────────────┐
│ ## Unsupervised Learning                    │ Chunk 5
│                                             │ Hierarchy: ["ML Fundamentals",
│ Unsupervised learning finds patterns...    │              "Unsupervised Learning"]
└─────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Preserves document structure
- ✅ Semantic sections intact
- ✅ Hierarchical context
- ✅ Natural boundaries

---

## 3️⃣ Context Chunking (With Surrounding Context)

**How it works**: Adds context from previous and next chunks.

```
                    ┌─── Context Before ───┐
                    │                      │
┌───────────────────▼──────────────────────▼───┐
│ [...artificial intelligence...]  ◄────────┐  │
│                                            │  │
│ ┏━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┓ │  │ Chunk 2
│ ┃ ## Supervised Learning                ┃ │  │ (Main Content)
│ ┃                                        ┃ │  │
│ ┃ Supervised learning uses labeled      ┃ │  │
│ ┃ data to train models. The algorithm   ┃ │  │
│ ┃ learns from examples with known       ┃ │  │
│ ┃ outcomes and makes predictions...     ┃ │  │
│ ┗━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━┛ │  │
│                                            │  │
│ [...Classification predicts...]  ◄────────┘  │
│                      │                        │
└──────────────────────┼────────────────────────┘
                       │
                       └─── Context After ───


When retrieving this chunk, you get:
┌────────────────────────────────────────────┐
│ Context Before: "...artificial             │
│   intelligence that enables systems..."    │
│                                            │
│ Main Content: "## Supervised Learning      │
│   Supervised learning uses labeled data    │
│   to train models..."                      │
│                                            │
│ Context After: "...Classification predicts │
│   discrete categories..."                  │
└────────────────────────────────────────────┘
```

**Benefits**:
- ✅ Context across boundaries
- ✅ Better semantic understanding
- ✅ Resolves ambiguous references
- ✅ Improved retrieval accuracy

---

## 4️⃣ Late Chunking (Contextual Embeddings)

**How it works**: Embeds full document first, then chunks while preserving context.

```
Step 1: Compute Full Document Embedding
┌─────────────────────────────────────────────────┐
│ [Full Document Text]                            │
│ # Machine Learning Fundamentals                 │
│ Machine learning is a subset...                 │
│ ## Supervised Learning...                       │
│ ### Classification...                           │
│ ### Regression...                               │
│ ## Unsupervised Learning...                     │
└─────────────────────────────────────────────────┘
                    │
                    ▼
        ┌─────────────────────┐
        │ Document Embedding   │
        │ [0.23, -0.15, 0.67,│
        │  0.82, -0.34, ...]  │
        └─────────────────────┘


Step 2: Chunk Text & Compute Individual Embeddings
┌──────────────────┐     ┌──────────────────┐
│ Chunk 1          │     │ Chunk Embedding  │
│ "ML is a subset" │────▶│ [0.45, -0.12,...]│
└──────────────────┘     └──────────────────┘


Step 3: Create Contextual Embedding (Blend)
┌─────────────────────────────────────────────────┐
│  Contextual Embedding = 70% Chunk + 30% Document│
│                                                 │
│  ┌─────────────┐      ┌──────────────┐        │
│  │ Chunk Emb   │      │ Document Emb │        │
│  │ [0.45,...]  │ 70%  │ [0.23,...]   │ 30%   │
│  └──────┬──────┘      └──────┬───────┘        │
│         │                    │                 │
│         ▼                    ▼                 │
│  ┌──────────────────────────────────┐         │
│  │   Blended Contextual Embedding   │         │
│  │   [0.38, -0.13, 0.48, ...]       │         │
│  │                                   │         │
│  │ ✓ Understands chunk content       │         │
│  │ ✓ Preserves document context      │         │
│  └──────────────────────────────────┘         │
└─────────────────────────────────────────────────┘


Result for each chunk:
┌────────────────────────────────────────┐
│ Chunk Text: "Supervised learning..."  │
│                                        │
│ Chunk Embedding: [0.45, -0.12, ...]   │
│ (understands local content)            │
│                                        │
│ Contextual Embedding: [0.38, -0.13,...]│
│ (understands local + global context)   │
└────────────────────────────────────────┘
```

**Benefits**:
- ✅ Best retrieval accuracy
- ✅ Global document context preserved
- ✅ Semantic coherence
- ✅ Handles specialized terminology better

---

## 📊 Side-by-Side Comparison

### Query: "What is supervised learning?"

**Token Chunking**:
```
Retrieved: "data to train models. The algorithm learns from..."
❌ Missing context about what supervised learning IS
❌ Starts mid-concept
```

**Markup Chunking**:
```
Retrieved: 
"## Supervised Learning

Supervised learning uses labeled data to train models. 
The algorithm learns from examples with known outcomes..."

✅ Complete section with heading
✅ Clear context
✅ Natural boundaries
```

**Context Chunking**:
```
Retrieved:
Context Before: "...ML is a subset of AI..."

Main: "## Supervised Learning
Supervised learning uses labeled data..."

Context After: "...Classification predicts discrete categories..."

✅ Understanding of where this fits in the document
✅ Connection to broader concepts
✅ Preview of what comes next
```

**Late Chunking**:
```
Retrieved: "Supervised learning uses labeled data..."

Embedding includes context about:
- Machine Learning being a subset of AI ✓
- Relationship to Classification & Regression ✓  
- Contrast with Unsupervised Learning ✓
- Overall document theme (ML fundamentals) ✓

✅ Most semantically accurate retrieval
✅ Understands relationships
✅ Best match for intent
```

---

## 🎯 Choosing the Right Strategy

### For Technical Documentation
```
Document Structure:
# API Reference
  ## Authentication
    ### OAuth2
    ### API Keys
  ## Endpoints
    ### GET /users
    ### POST /users

✅ Use MARKUP CHUNKING
   - Preserves API structure
   - Each endpoint is a complete chunk
   - Hierarchy shows relationships
```

### For Long Narratives
```
Document Type: Research Paper / Blog Post

"...Previous work in NLP focused on RNNs. However, 
these models had limitations with long sequences. 
The transformer architecture addressed this by..."

✅ Use CONTEXT CHUNKING
   - Connects ideas across chunks
   - Understands "these models" reference
   - Preserves narrative flow
```

### For Critical Accuracy
```
Use Case: Medical/Legal Documents
Requirement: Highest possible retrieval accuracy

"The dosage of 50mg should be administered twice 
daily. Contraindications include..."

✅ Use LATE CHUNKING
   - Most accurate embeddings
   - Understands full medical context
   - Critical for safety
```

---

## 💡 Hybrid Approaches

You can combine strategies for best results:

### Approach 1: Markup + Context
```
Step 1: Use Markup to identify sections
┌─────────────────┐
│ # Introduction  │ Section 1
└─────────────────┘
┌─────────────────┐
│ ## Background   │ Section 2
└─────────────────┘

Step 2: Add context between sections
┌─────────────────────────────────────┐
│ Section 2: "## Background"          │
│ Context from Section 1: "...intro..."│
│ Context from Section 3: "...methods"│
└─────────────────────────────────────┘
```

### Approach 2: Markup + Late
```
Step 1: Use Markup for large sections
┌────────────────────────────┐
│ ## Supervised Learning     │ Large section
│ [2000 characters]          │
└────────────────────────────┘

Step 2: Apply Late Chunking to large sections
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Sub-chunk 1  │  │ Sub-chunk 2  │  │ Sub-chunk 3  │
│ w/ contextual│  │ w/ contextual│  │ w/ contextual│
│ embeddings   │  │ embeddings   │  │ embeddings   │
└──────────────┘  └──────────────┘  └──────────────┘

Result: Structure preservation + Best embeddings
```

---

## 📈 Performance Visualization

```
Retrieval Accuracy ▲
                  │
            100%  │                          ●  Late
                  │                     ●  
             90%  │                ●    Context
                  │           ●   
             80%  │      ●    Markup
                  │  ●
             70%  │  Semantic
                  │●
             60%  │ Token
                  │
                  └────────────────────────────────▶
                   Speed (Faster ──────▶ Slower)


Memory Usage     ▲
                  │
            High  │                          ●  Late
                  │
          Medium  │                ●  Context
                  │           ●  
             Low  │      ●    Semantic/Markup
                  │  ●
        Very Low  │  Token
                  │
                  └────────────────────────────────▶
                   Complexity (Simple ──▶ Complex)
```

---

## 🔍 Real Example Output

Given this query: **"How does supervised learning differ from unsupervised learning?"**

### Token Chunking Result
```
Score: 0.72
Chunk: "learning uses labeled data to train models. The 
algorithm learns from examples with known outcomes and makes"

⚠️ Missing: What IS supervised learning
⚠️ Missing: Comparison to unsupervised
```

### Markup Chunking Result
```
Score: 0.81
Chunk: "## Supervised Learning

Supervised learning uses labeled data to train models. The 
algorithm learns from examples with known outcomes..."

Section Path: "ML Fundamentals > Supervised Learning"

✓ Complete section
✓ Clear hierarchy
❌ Missing: Direct comparison
```

### Context Chunking Result  
```
Score: 0.87
Main: "## Supervised Learning
Supervised learning uses labeled data..."

Context After: "## Unsupervised Learning
Unsupervised learning finds patterns in unlabeled data..."

✓ Has both concepts
✓ Natural comparison possible
✓ Connected information
```

### Late Chunking Result
```
Score: 0.94
Chunk: "## Supervised Learning
Supervised learning uses labeled data to train models..."

Contextual Embedding captures:
- Relationship to unsupervised learning ✓
- Position in ML fundamentals ✓
- Contrast between labeled/unlabeled ✓
- Overall document theme ✓

✓ Highest score
✓ Best semantic match
✓ Most relevant to query intent
```

---

## 🎓 Summary

| Strategy | Visual Metaphor | Best For |
|----------|----------------|----------|
| **Token** | Cutting paper with ruler | Quick prototyping |
| **Semantic** | Cutting along dotted lines | General purpose |
| **Markup** | Cutting along perforations | Structured docs |
| **Context** | Cutting with transparent tape | Long narratives |
| **Late** | 3D holographic cutting | Maximum accuracy |

---

## 📚 Try It Yourself

Run the demo to see these strategies in action:

```bash
python examples/chunking_strategies_demo.py
```

The demo will show you:
1. How each strategy processes the same document differently
2. What metadata each strategy provides
3. Comparative statistics
4. Real chunk examples

---

**Ready to implement? See:**
- Quick Start: `docs/CHUNKING_QUICK_REFERENCE.md`
- Full Guide: `docs/CHUNKING_STRATEGIES_GUIDE.md`
- Examples: `examples/chunking_strategies_demo.py`

