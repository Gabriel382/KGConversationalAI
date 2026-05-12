# Canonical schema

`schemas/kgconvai.schema.json` defines a strict JSON shape:

```json
{
  "version": "1.0",
  "namespace": "http://kgconvai.local/data#",
  "states":      [ { "id": "start" } ],
  "intents":     [ { "id": "greet" } ],
  "transitions": [ { "from": "start", "intent": "greet", "to": "ask_information" } ],
  "faqs":        [ { "id": "...", "intent": "...", "question": "...", "answer": "..." } ],
  "templates":   [ { "intent": "...", "text": "..." } ],
  "entities":    [ { "id": "...", "type": "Caller", "properties": {} } ],
  "relations":   [ { "from": "...", "type": "...", "to": "..." } ]
}
```

Every load through `KGData.from_json` validates against the schema before
returning, so backend code can assume the data is well-formed.

`KGData.to_json` **canonicalises** the output (lists sorted by a stable key,
dict keys sorted) — this is what makes round-tripping byte-identical.
