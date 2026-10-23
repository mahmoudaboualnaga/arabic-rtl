# Why Arabic text gets scrambled

## The mechanism

Text is stored in reading order (first word first). The viewer then lays each paragraph out with the Unicode Bidirectional Algorithm:

1. **Paragraph direction.** Where the app doesn't set it (chat bubbles, Markdown, Claude Docs blocks, `dir="auto"`), it is taken from the paragraph's **first strong letter**: Arabic/Hebrew → right-to-left, Latin → left-to-right. Digits, spaces, punctuation, `*`, `-`, `#`, emoji are "weak" or "neutral" and are skipped.
2. **Runs.** Inside the paragraph, Arabic runs read right-to-left and Latin runs left-to-right.
3. **Neutrals.** Punctuation and spaces between two runs of different directions take the **paragraph** direction. At the end of a paragraph they always take the paragraph direction.

So:

- An Arabic paragraph that opens with `PCBWay` becomes a left-to-right paragraph. Its Arabic runs are then placed left-to-right as blocks: the sentence reads in the wrong order, the line starts at the left, and the last line wraps under the wrong end.
- An Arabic paragraph that ends with `Idea Vault.` — the period is neutral, follows the Latin run, and lands next to it on the left side of the line in the middle of the text instead of at the sentence end.
- `PCB، CNC، 3D` inside Arabic: each comma sits between two Latin runs, so it takes the Latin direction and the terms read as one left-to-right chunk in an order the reader doesn't expect.
- `15–25%` inside Arabic can flip to `25–15%` visually.

## The invisible marks

| Mark | Code | Use |
|---|---|---|
| RLM (right-to-left mark) | U+200F | Invisible strong RTL letter. Put at the start of a block that must open with Latin, or after a Latin term before punctuation. |
| LRM (left-to-right mark) | U+200E | The reverse: inside an English sentence that contains Arabic. |
| RLI … PDI | U+2067 … U+2069 | Isolate an Arabic phrase inside English text so it can't disturb its surroundings. |
| LRI … PDI | U+2066 … U+2069 | Isolate an English term or number inside Arabic text. Supported by modern browsers; older apps may show boxes — prefer RLM. |

RLM/LRM are copied along when the user copies the text; that's harmless in documents and chat, but avoid them inside code, URLs, file names and spreadsheet formulas.

## Before / after (from real replies that broke)

**Opening with an English name**

Broken: `**PCBWay باختصار:** هي مصنّع شكله منصة. عندها 5 مصانع، منهم اتنين للـ PCB...`
Fixed: `**باختصار، شركة PCBWay** مصنّع شكله منصة، عنده 5 مصانع، منهم اتنين لتصنيع الـ PCB...`

**Ending with an English term**

Broken: `ملف فيه جدول الـ25 منافس، والنموذج المالي، ووصف الفكرة في الـ Idea Vault.`
Fixed: `ملف فيه جدول الخمسة وعشرين منافس، والنموذج المالي، ووصف الفكرة في سجل الأفكار (Idea Vault) عندك.`

**File name inside the sentence**

Broken: `التقريرين جاهزين، وملف Industrial_Marketplace_Competitor_Tracker_and_Model.xlsx فيه جدول المنافسين.`
Fixed:
```
التقريرين جاهزين، ومعاهم ملف الإكسل اللي فيه جدول المنافسين والنموذج المالي:
`Industrial_Marketplace_Competitor_Tracker_and_Model.xlsx`
```

**List of English terms**

Broken: `بيقدموا PCB، CNC، 3D printing.`
Fixed: `بيقدموا تصنيع الـ PCB وتشغيل CNC والطباعة ثلاثية الأبعاد.`

**Range and percentage**

Broken: `علاوة 15–25% مقارنة بالورشة.`
Fixed: `علاوة من 15 إلى 25% مقارنة بالتعامل المباشر مع الورشة.`

**Numbered list in Claude Docs**

Broken: list items that open with a number or English word render left-to-right with the number on the left.
Fixed: short paragraphs with a bold Arabic label (`**الخطوة الأولى:** توثيق عشر ورش...`), or a two-column table (`الخطوة` | `التفاصيل`), or list items that each start with RLM + an Arabic word.
