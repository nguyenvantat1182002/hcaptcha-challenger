Solve the challenge, use [0,0] ~ [2,2] to locate 9grid, output the coordinates of the correct answer as json.

Follow the following format to return a coordinates wrapped with a json code block:
```json
{
  "challenge_prompt": "please click on the largest animal",
  "coordinates": [
    {"box_2d": [0,0]},
    {"box_2d": [1,2]},
    {"box_2d": [2,1]}
  ]
}
```

## SUPERVISOR GUIDANCE (if provided)

If the user message contains a section titled "SUPERVISOR GUIDANCE", treat it as **high-priority expert instructions** that override ambiguity. This guidance describes the specific visual characteristics (shape, color, category) of the target objects. Use it to:
- Know exactly **what** objects to look for in each grid cell before analyzing
- Resolve any ambiguity in the challenge prompt
- Filter out distractors explicitly mentioned in the guidance
