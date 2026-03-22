# PCSL JSON-LD Schema Reference

PCSL context objects use JSON-LD for semantic interoperability. This document maps PCSL namespaces to standard schemas where available.

## Context Definition (`context.jsonld`)

```json
{
  "@context": {
    "pcsl": "https://pcsl.dev/ns/1.0#",
    "schema": "http://schema.org/",
    "identity": "schema:Person",
    "name": "schema:name",
    "profession": "schema:jobTitle",
    "location": "schema:address",
    "skills": {
      "@id": "pcsl:skills",
      "@container": "@set"
    },
    "projects": {
      "@id": "schema:Project",
      "@container": "@list"
    },
    "goals": "pcsl:goals",
    "decisions": "pcsl:decisions"
  }
}
```

## Namespace Definitions

### Identity
Maps to `schema:Person`. Fields:
- `name`: `schema:name`
- `profession`: `schema:jobTitle`
- `education`: `schema:EducationalOccupationalCredential`

### Skills
List of user's core competencies. Recommended formats:
- Simple list: `["Python", "React", "AI Optimization"]`
- Object-based: `[{"name": "Python", "level": "expert"}]`

### Projects
List of `schema:Project` objects. Fields:
- `name`: `schema:name`
- `status`: `schema:creativeWorkStatus`
- `stack`: `pcsl:techStack` (list)
- `goal`: `schema:abstract`

### Preferences
Personalized AI behavior settings. Fields:
- `communication_style`: `pcsl:style`
- `explanation_depth`: `pcsl:depth`
- `tone`: `pcsl:tone`
- `language`: `schema:inLanguage`
