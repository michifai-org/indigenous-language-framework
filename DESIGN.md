# Design

This document records what the framework is trying to do, who it is for, and the reasoning behind its choices. It is a working document. Where something is a guess rather than something learned, it says so.

## The problem

Indigenous language programs often have the essential ingredients: speakers, recordings, archival material, and committed learners. What many lack is a **curriculum**, a deliberate sequence that takes a learner from first sounds to confident use. Designing one is slow, needs both linguistic and teaching expertise, and is usually done from scratch by each program.

The framework aims to lower the cost of that step.

It will not solve the harder problems: too few fluent speakers, too little documentation, too little funding and time. It helps most where material already exists and needs to be organized into teaching.

## Principles

1. **Structure from the framework, content from the community.** We never supply vocabulary, grammar, stories or cultural knowledge for any language.
2. **Data sovereignty comes first.** Community content stays under community control. See PROTOCOLS.md.
3. **Built for coordinators and teachers, not programmers.** If a step needs a developer, it is a design failure.
4. **Works offline and on paper.** Many communities have unreliable internet. Everything must run without a connection and print cleanly.
5. **No assumed orthography or grammar.** Languages differ, and some have several writing systems. The community declares its own.
6. **Culture is part of the method.** Speaker and elder involvement and place-based content are required parts of the templates, not optional extras.
7. **Say what is known and what is not.** Claims about method and effectiveness stay modest until pilots give evidence.

## Origin of the method

The method is inspired by the author's experience in the Chinuk Wawa program at Lane Community College in Oregon. This is one learner's experience, not a formal study of that program, and the framework is not affiliated with or endorsed by Lane or the Confederated Tribes of Grand Ronde.

The features that stood out, and the component each becomes:

| Feature of the experience | Framework component |
|---|---|
| Each lesson built on the last, from basics upward | Scope and sequence template; every lesson declares what it assumes and what it introduces |
| Speaking, listening, reading and writing mixed together, from single words to sentences to short essays of roughly 250-500 words | Lesson template with a slot for each skill |
| Grammar and word order built up gradually and reinforced through speaking and writing | Grammar tagging; exercises must reuse earlier structures |
| Real objects and stories from the learners' own surroundings | Place-based prompts in every unit |
| Assigned partners in the first year, with practice twice weekly during semesters | Partner practice guide: pairing, schedule, activities, check-in log |
| Visiting speakers on culture and history | Speaker-visit guide: protocol, preparation, linking the visit to unit vocabulary |
| Alphabet and sounds reviewed at the start of every class | Opening routine in the lesson template, with sound-by-sound audio |

## Where this will not transfer directly

Chinuk Wawa has an established orthography, a textbook, a dictionary, extensive recordings and an institutional program. Many languages will have less. Consequences:

- **The orthography is declared per community**, and more than one may be allowed.
- **Grammar progression is authored by the community.** The framework offers a worksheet for deciding what to teach first, not the order itself.
- **Levels are defined by available material**, not by a fixed target such as essay length. Essay-length texts need a body of material that some languages do not yet have.
- **Pedagogy may need adapting.** A method that worked well for one language and setting is a hypothesis for another. Pilots exist to test that.

## First pilots

1. **Chinuk Wawa.** The author knows this language and method firsthand and has existing work on archival Chinuk Wawa recordings.
2. **Southern (heritage) Michif.** The author's business is Red River Métis-owned. The choice of Southern or heritage Michif is the author's starting point and is open to correction by Michif speakers and educators. It will need real community input; we do not assume how Michif should be structured.

Pilots are for feedback and testing, not for claiming success.

## Repository structure (planned)

```
README.md              what this is, who it's for
DESIGN.md              this document
PROTOCOLS.md           data sovereignty and what never goes in this repo
LICENSING.md           what is licensed, and what is not
docs/                  method guide, published with GitHub Pages
templates/
  scope-and-sequence/
  unit/
  lesson/
  speaker-visit/
  partner-practice/
schema/                structure for community content
tools/                 scripts: content in, lessons, flashcards, PDFs out
examples/              demo in a clearly fictional language
```

## How the GitHub features are used

- **Template repository.** The main distribution method. A community uses "Use this template" to make its own private copy.
- **Pages.** Public site for the method guide, a demo and, later, a browser-based builder. Pages serves static files only.
- **Discussions.** A place for practitioners to talk to each other.
- **Issues with templates.** Feedback and requests in a form non-programmers can fill in.
- **Actions.** Automatically build lessons, flashcards and PDFs when content changes.
- **Wiki.** Not used. Documentation lives in the repo so it is versioned and reviewable.

Details of private-repository and Pages availability change over time and should be checked on GitHub's current documentation before we depend on them.

## Phases

1. **Foundation.** README, DESIGN, PROTOCOLS, LICENSING, template-repository setup.
2. **Toolkit v0.1.** Templates, scope-and-sequence worksheet, content schema, method guide, fictional demo.
3. **Builder scripts.** Content in; lessons, flashcards and printable PDFs out. Test the schema against real audio-based material.
4. **Pilots.** Chinuk Wawa and Southern Michif groups use the toolkit; feedback drives v0.2.
5. **Online tool.** A browser-based builder at michifai.ca, built on what the toolkit has proven.

## Governance

The repository is owned and maintained by its creator. If it gains use, an advisory group of Indigenous language leaders may be formed to guide direction. No such group exists yet, and none is implied.

## Open questions

- Which Michif community and educators will advise on the Southern Michif pilot?
- What is the right minimum content schema that handles several orthographies without becoming unusable?
- How should audio be handled so recordings stay inside the community's private copy?
- What does a first-year learner need from partner practice if there is no cohort, only a few individuals?
- How do we evaluate whether the method works in a new language, and who decides?
