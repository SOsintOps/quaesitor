# Case Study: Blood of the Dragon

A complete link analysis exercise on the family network of *A Song of Ice and Fire*, the world of *Game of Thrones* and *House of the Dragon*: from a scraped table of 3,653 characters to a graded chart, the questions of association analysis, competing hypotheses and the list of intelligence gaps. It follows the steps of the [Link Analysis Guidelines](link-analysis.md) and uses only what Quaesitor does, plus one script for the measures the program does not compute.

The case is fiction, which is the point: every reader can check the answers, nobody's privacy is at stake, and the source has exactly the defects of a real one.

## Source and Notice
The idea and the data come from Tomaz Bratanic, *Investigate family connections between House of the Dragon and Game of Thrones characters* ([Towards Data Science on Medium](https://medium.com/data-science/investigate-family-connections-between-house-of-dragon-and-game-of-thrones-characters-ff2afd5bdb82)), with its two notebooks in [tomasonjo/blogs/ice&fire](https://github.com/tomasonjo/blogs/tree/master/ice%26fire) (Neo4j import, then Cypher and Graph Data Science analysis). The table itself is [`ice_fire/characters.tsv`](https://github.com/tomasonjo/blog-datasets/tree/main/ice_fire) in tomasonjo/blog-datasets: one row per character scraped from [A Wiki of Ice and Fire](https://awoiaf.westeros.org) (AWOIAF), with allegiances, culture, father, mother, spouse, books, seasons, birth, death and titles.

The article (10 November 2022) builds the graph in Neo4j, explores it in Neo4j Bloom with two search phrases (the shortest family path between two characters, all the ancestors of one) and runs the Weakly Connected Components algorithm on the family links. It reports 3,653 characters and 563 factions, and a largest family component of 785 people.

The text of AWOIAF is published under a Creative Commons Attribution-ShareAlike licence ([copyrights page](https://awoiaf.westeros.org/index.php/A_Wiki_of_Ice_and_Fire:Copyrights)), version 3.0 according to the article; the two data files of this case are derived from it and carry the same licence. Every node keeps the address of its wiki page in its card, which is the attribution the licence asks for. The tomasonjo repositories state no licence; nothing of their code is copied here, only the questions of the notebooks.

## The Files
| File | What it is |
| :--- | :--- |
| `esempi/got_kinship.csv` | The chart: the largest family network of the source, 698 people and 1,108 links, one row per link. |
| `esempi/got_kinship_hypotheses.csv` | Three hypothesised links and one open question, kept apart from the source on purpose. |
| `scripts/casestudy/got_kinship.py` | Builds both files from the scraped table and prints every number quoted on this page. Standard library only. |

Run `python scripts/casestudy/got_kinship.py` to download the table and rebuild the files; pass the path of a local `characters.tsv` to work offline. The findings come out as Markdown on standard output.

## The Tasking
The Small Council wants to know, before the next succession crisis, how the great houses are bound to one another by blood and marriage. Four questions:

1. Who holds the network together, and whose removal would split it?
2. How is the Lannister family tied to the old Targaryen kings of *House of the Dragon*?
3. Which claims rest on a parentage the records themselves contradict?
4. Who are the parents of Jon Snow?

The focus of the chart (step 2 of the method) is kinship: father, mother and spouse links only. Allegiance, culture and the books a character appears in stay out; a chart about everything shows nothing.

## Evaluate Before You Link
The source is a fan wiki of a novel, scraped by a third party. Graded with the 4 x 4 system, AWOIAF is a **B** source (most of its information has proved reliable; it cites the books chapter by chapter), and each link is at best a **2**: the wiki did not witness the births, it reports what the books report, and the books report what their characters believe. Some of those characters lie.

Before any line is drawn the table has to be cleaned, and every cleaning step is a judgement worth writing down. The script prints these counts; the reasons are below.

| Defect found | Count | Treatment |
| :--- | ---: | :--- |
| Names with a title glued on (`LadyJoanna Lannister`, `KingAerys II Targaryen`), a citation mark (`Aegon Targaryen[1]`) or a stray space | 60 | Cleaned. |
| Homonyms: different people, one name (six different *Aegon Targaryen*, two *Lyanna Stark*) | 393 | Renamed after their wiki page, `Aegon Targaryen (son of Rhaegar)`. Quaesitor merges nodes with the same name, so without this step six people would collapse into one. |
| One page reached as `http://` and `https://` (Daenerys Targaryen among them) | 4 | One key per page, whatever the scheme. |
| One person under two pages: a linked page with no row whose title is the name of exactly one row (`Olenna Tyrell` is the row of `Olenna Redwyne`) | 8 | Merged. Catelyn Tully into Catelyn Stark (the notebook's own merge) and Lysa Tully into Lysa Arryn are merged by hand. |
| A house page in place of a parent (`House Blackwood` as the father of a Blackwood) | 65 | Dropped. Left in, `House Blackwood` becomes a "father" who joins unrelated people, and the shortest path from Jon Snow to Daenerys runs through it. |
| A group, place, god or trade in place of a person (`Smallfolk` as a mother, `Salt Wife`, `Septon`, two rivers) | 38 | Dropped. `Smallfolk`, the mother of every bastard of unknown mother, made Mya Stone look like one of the ten most central people of Westeros. |
| A page linked to itself | 218 | Dropped. |
| Two different pages with the same name, father and son (Jon Umber and the Smalljon) | 11 | **Kept.** The notebook deletes every link between two equal names and loses these true links with the self-links. |
| A marriage recorded on both sides | 235 | Counted once. |
| Dates with the dash of a range lost in the scrape (`211219 AC` for 211–219 AC) | – | Left as they are in the card notes; read them with care. |

What is left: 1,452 people and 1,694 links in 236 separate families. The largest family network holds 698 people; the next has 24. The chart is that largest network.

Six more pages could not be classified from the data alone (`Cymmeri`, `Doshi`, `Gipps`, `Kayce`, `Mhaegen`, `Zoqora`) and are kept as people: an open point for whoever checks the wiki.

## Importing the Chart
1. Create a case (one per question set: this one could be *Blood of the Dragon*).
2. **Import CSV/Excel**, drop `esempi/got_kinship.csv`. The preview reads the columns by their headers: two people per row, the relation, the arrow, the line style, the colour, and a Follow the Money **Family** relation with its `relationship` (father, mother, spouse).
3. **Import.** Expected result: 698 nodes and 1,108 connections, no rows with errors.

The conventions of the file: a parent link points from the child to the parent (blue for a father, pink for a mother), a marriage is a red line without arrows. Every card carries birth, death, titles and allegiance in its notes and the wiki page as its link. Jon Snow is marked as the **target** of the case.

A link is drawn **dashed** with the label `father (conflicting records)` or `mother (conflicting records)` when the source gives the same child two fathers or two mothers. Neither of the two can be confirmed, and the method says an unconfirmed link is never drawn solid. There are 36 such links.

## Question 1: Who Holds the Network Together?
Step 5 of the method counts the links of each entity. In Quaesitor the count is the **Conn.** column of the export and the filter **Show nodes with** under *Connections*, which lists every degree present in the graph with the number of nodes that have it: choose `= 45 · 1 nodes` and Walder Frey appears with his neighbours; **Hide the others** leaves him alone.

| Most links (degree) | | Most shortest paths through them (betweenness) | |
| :--- | ---: | :--- | ---: |
| Walder Frey | 45 | Aegon V | 84,707 |
| Aegon IV | 19 | Steffon Baratheon | 83,562 |
| Alysanne Targaryen | 15 | Rhaelle Targaryen | 82,090 |
| Cregan Stark | 15 | Walder Frey | 81,661 |
| Jaehaerys I | 15 | Cersei Lannister | 78,569 |
| Alyssa Velaryon | 12 | Maekar I | 77,723 |
| Elaena Targaryen | 12 | Daeron II | 76,137 |
| Aerys II Targaryen | 11 | Robert I | 75,157 |
| Leyton Hightower | 11 | Tywin Lannister | 73,979 |
| Robert I | 11 | Genna Lannister | 59,431 |

The two lists answer different questions. Degree finds the prolific: Walder Frey's 45 links are eight wives, 36 children and a father; Aegon IV's 19 are mostly children, a good many of them bastards. Betweenness finds the **corridor**: Aegon V, his daughter Rhaelle, her son Steffon Baratheon and his son Robert form the one line through which most kinship paths between the old Targaryen kings and the people of *Game of Thrones* must pass, and the Lannisters (Tywin, his sister Genna, his daughter Cersei) are the corridor between Robert and the rest of the realm. Quaesitor does not compute betweenness; the script does, and the answer is then checked on the chart with **H+Click** on each of those nodes.

**Cut points** answer the manual's question *which people, if removed, would sever the network?* The script removes each of the forty most central people in turn and counts who is left outside the largest piece:

| Removed | Cut off |
| :--- | ---: |
| Walder Frey | 55 |
| Margaery Tyrell | 46 |
| Alerie Hightower | 30 |
| Aegon IV | 15 |
| Robert I | 13 |

Walder Frey is a cut point for an obvious reason: half his house hangs on him alone. Margaery Tyrell is the finding. In this source 46 people of the Reach (Hightowers, Redwynes, Tyrells, Florents, Tarlys, Fossoways and their in-laws) are tied to the royal family only through her three marriages, to Renly, Joffrey and Tommen. One woman is the alliance. To see it, **N+Click** Margaery: the Tyrell side is left without a single line to the rest of the graph; **Show 1 hidden** brings her back.

## Question 2: From Tyrion to the Old Kings
The first notebook query asks for the shortest kinship path from Tyrion Lannister to Viserys I, the king whose succession opens *House of the Dragon*. The script finds it in **12 hops**:

Tyrion Lannister → his mother Joanna Lannister → her daughter Cersei → her husband Robert I → his father Steffon Baratheon → his mother Rhaelle Targaryen → her father Aegon V → his father Maekar I → his father Daeron II → his father Aegon IV → his father Viserys II → his mother Rhaenyra Targaryen → her father Viserys I.

The path is the corridor of Question 1, and the article finds the same entry point: from Tyrion through Cersei and Robert to Robert's grandmother Rhaelle Targaryen.

The article then asks how closely Robert is related to the king he overthrew, Aerys II, and names Betha Blackwood as their most recent common ancestor. The data say a little more: Robert and Aerys II have **two** most recent common ancestors at the same distance, the couple Aegon V and Betha Blackwood (Robert's great-grandparents, Aerys's grandparents); the shortest path, 5 hops, runs through Aegon V. A shortest path shows one road, not every road: to answer a question about ancestry, look at all the paths. **Highlight all paths** with **Max hops** 5 shows four, not two, because the parents of Aerys II, Jaehaerys II and Shaera, were brother and sister, both children of Aegon V and Betha: every road from Rhaelle's parents to Aerys doubles. Quaesitor searches paths of at most six hops (**Max hops**), and it highlights *all* the paths within that limit, not only the shortest. A twelve-hop path is therefore checked in segments, with intermediate people chosen from the corridor:

1. Search and **Ctrl+Click** Tyrion Lannister and Rhaelle Targaryen; **Max hops** 5; **Highlight all paths**. The shortest segment is 5 hops.
2. **Clear**, then Rhaelle Targaryen and Daeron II with 3 hops; then Daeron II and Viserys I with 4.
3. **Hide the rest** on each result and **Save view** with a dated name (*Q2 segment 1, 2026-10-13*): the views are the revision record the method asks for.

Shorter answers fit in one search: Sansa Stark to Cersei Lannister is 3 hops, two paths (through her husband Tyrion and either of his parents, Tywin or Joanna); Margaery Tyrell to Sansa Stark is 5, with eight paths of up to five hops, all through Joffrey or Tommen, the Lannisters and Tyrion. Four of the eight pass through Jaime as the boys' father, a dashed line: a path is only as confirmed as its weakest link, so report the four that run through Cersei. The first segment of the Tyrion path above also has two variants, through Tywin or through Joanna.

The second notebook query, the ancestry of Margaery Tyrell, is three generations in this source: Mace Tyrell and Alerie Hightower; Luthor Tyrell, Olenna Tyrell and Leyton Hightower; Runceford Redwyne. Highlight the paths from Margaery to Runceford Redwyne and to Leyton Hightower, **Hide the rest**, and choose the **Hierarchical** layout to read it as a tree.

The article adds that Margaery is said to be distantly related to Otto and Alicent Hightower of *House of the Dragon*, "although no explicit connections are defined". The cleaned data confirm the gap: Margaery shares no ancestor with either of them, and the only path to Alicent (11 hops) runs through Margaery's marriage to Renly, the Baratheon–Targaryen corridor and Alicent's marriage to Viserys I, not through the Hightowers at all. A claim of kinship with no line behind it goes in the list of gaps, not on the chart.

The last notebook query looks for marriages between a child of a Targaryen and a child of a Stark. In this source there is one: Jacaerys Velaryon, son of Rhaenyra Targaryen, with Sara Snow, daughter of Rickon Stark. Hold on to Jacaerys.

## Question 3: Claims Resting on Contradicted Parentage
Turn on the dashed links (or read them in the script's output): nineteen children have two fathers or two mothers in the source. Read them as an analyst, not as a database cleaner, because they fall into two very different groups.

**The source records a contested claim.** Joffrey, Myrcella and Tommen Baratheon have two fathers: Robert I and Jaime Lannister. Jacaerys, Lucerys and Joffrey Velaryon, the sons of Rhaenyra, have two: Laenor Velaryon and Harwin Strong. Addam and Alyn of Hull: Laenor or Corlys Velaryon. Viserys Plumm: Ossifer Plumm or Aegon IV. Jon Snow: two mothers, Wylla and Ashara Dayne. Every one of these is a succession dispute; the first two groups are the plots of *Game of Thrones* and *House of the Dragon*. The wiki, being a good source, records both claims, and the scraper flattened "officially X, rumoured Y" into two equal links. The dashed line puts the doubt back.

**The source records an error.** Eight Freys have both `Walder Frey` and `Walder Frey (son of Ryman)` as father: one link points to the wrong homonym. Grade them low and leave them dashed; they change no answer here.

The finding for the Council: the claims of Robert's three children and of the three sons Rhaenyra bore while married to Laenor rest on a parentage that the realm's own records contradict. In both cases the doubt fed a war.

## Question 4: The Parents of Jon Snow
The card of Jon Snow says his father is Eddard Stark and his mother is Wylla or Ashara Dayne. Import `esempi/got_kinship_hypotheses.csv` into the same case. It adds, dashed and purple, the hypothesis the source does not record (Rhaegar Targaryen as father, Lyanna Stark as mother, the two of them married), and a text node *Open question: who are the parents of Jon Snow?* linked to Jon and to every candidate parent, the method's way of keeping a collection gap on the chart.

Lay the evidence of the books against the three hypotheses, as in the Analysis of Competing Hypotheses: ++ consistent, – inconsistent, · neutral.

| Evidence | Eddard and Wylla | Eddard and Ashara | Rhaegar and Lyanna |
| :--- | :---: | :---: | :---: |
| Eddard claims Jon as his bastard and never names the mother, even to his wife | ++ | ++ | ++ |
| Edric Dayne says his wet nurse Wylla is Jon's mother | ++ | – | · |
| The rumour of Ashara Dayne, heard by Catelyn | – | ++ | · |
| Eddard is remembered as the most honourable man of his generation, faithful to his wife | – | – | ++ |
| Lyanna dies in a "bed of blood" at the Tower of Joy after making Eddard promise something | · | · | ++ |
| Eddard brings the infant home from the war in the south, the war in which Lyanna died | · | · | ++ |

The first row fits every hypothesis and so proves nothing; the method throws such evidence out of the scoring. What remains is least inconsistent with Rhaegar and Lyanna, which is the hypothesis the novels lead to and the one the television series confirms (season 6 and season 7 finales). The chart shows what it changes. Select Jon Snow and Daenerys Targaryen and **Highlight all paths**:
- on the source alone, before the second import, Quaesitor finds no path even with **Max hops** 6: the script finds the shortest at 12 hops, through Sansa, Tyrion, the Lannisters and the Baratheon corridor;
- with the hypothesis imported and **Max hops** 3, two paths: Jon → Rhaegar → Aerys II → Daenerys, and the same through their mother Rhaella. Jon is not a distant in-law of everybody; he is Daenerys's nephew, and the son of the heir of Aerys II.

That is why a hypothesised link is drawn and never mixed with the source: it changes the most important answer of the case. Save the two states as two views.

## Intelligence Gaps
The written product ends with what is still unknown and where to look:
- **Jon Snow:** no record of the marriage of Rhaegar and Lyanna in the source; the witness is Howland Reed. Collection: the wiki pages of Howland Reed and of the Tower of Joy, the series' season 7 finale.
- **The children of Cersei and of Rhaenyra:** grade each of the two fathers separately; the source should say which claim is official and which rumoured.
- **The Frey homonyms:** check on the wiki which Walder Frey is the father of each of the eight.
- **Six unclassified pages** (`Cymmeri`, `Doshi`, `Gipps`, `Kayce`, `Mhaegen`, `Zoqora`): person or place?
- **Margaery Tyrell and the Hightowers of *House of the Dragon*:** a kinship the article reports as hearsay, with no ancestor in common in the data. Collection: the Hightower family tree on the wiki, between Otto and Leyton.
- **The source's reach:** 105 people exist only as a link from someone else's row, with no page and no notes of their own.

## Comparison with the Notebooks
The article and its notebooks answer the same questions in Neo4j, and their largest family component has 785 people; an early version of the build script that followed the notebook's rules found the same 785. The cleaning described above brings it to 698. Three differences matter for an analyst:
- they delete every link between two equal names, which removes the father–son links of homonyms together with the true self-links;
- they keep house pages, groups and places as people, which creates false bridges (the Jon Snow path through `House Blackwood`, the centrality of Mya Stone);
- they merge or keep duplicates by hand (Catelyn) where a rule exists (a linked page without a row whose title is exactly one row's name is a redirect).

None of this is a criticism of a blog post that set out to show Cypher, not to grade a source. It is the difference between computing an answer and standing behind it.

## What the Program Does and Does Not Do Here
Quaesitor carried the mechanics: identity of the nodes, the typed Family relations, dashed and solid lines, the degree filter, paths up to six hops, the target, the open question as a text node, saved views per revision. It did not compute betweenness, cut points or paths longer than six hops: the script does, and its numbers are checked on the chart. It did not grade the source or choose between the hypotheses: those were the analyst's judgements, written above, and the report remains the product.
