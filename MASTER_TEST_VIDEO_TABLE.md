# ClipScribe Master Test Video Table

*Last Updated: 2025-06-27*

This document contains all approved test videos for ClipScribe development and testing, organized by category and testing purpose.

## 📖 **Series (Same Channel + Same Topic)**

### Series 1: My Chemical Romance Documentary Series
**Channel:** Same  
**Topic:** Music documentary series  
**Testing Purpose:** Series detection, narrative flow, music industry analysis  

| Video | URL | Title | Notes |
|-------|-----|-------|-------|
| Part 1 | https://youtu.be/gxUrKV33yys?si=iYMMiwq0mdOZmnWj | The Tragic Early Days of My Chemical Romance | Early band history |
| Part 2 | https://youtu.be/2jlsVEeZmVo?si=DIFBEdOFjIx-M7er | The Revenge of My Chemical Romance | Band evolution |
| Part 3 | https://youtu.be/o6wtzHtfjyo?si=p_5hEh_Mjr7wDhLY | The Haunting Beauty of The Black Parade | Peak period |
| Part 4 | https://youtu.be/0ESDiJdCfxY?si=8znBwJj-5S1waVRQ | Danger Days - The End of My Chemical Romance | Band conclusion |

### Series 2: Pegasus Spyware Investigation 
**Channel:** FRONTLINE PBS  
**Topic:** Investigative journalism, surveillance, technology  
**Testing Purpose:** Multi-part investigation, entity tracking across episodes  

| Video | URL | Title | Notes |
|-------|-----|-------|-------|
| Part 1 | https://www.youtube.com/watch?v=6ZVj1_SE4Mo&t=65s | Global Spyware Scandal: Exposing Pegasus Part One | Investigation setup |
| Part 2 | https://www.youtube.com/watch?v=xYMWTXIkANM | Global Spyware Scandal: Exposing Pegasus Part Two | Investigation conclusions |

### Series 3: Iran-Saudi Arabia Relations
**Channel:** FRONTLINE PBS  
**Topic:** Geopolitics, Middle East, international relations  
**Testing Purpose:** Historical timeline extraction, geopolitical entity relationships  

| Video | URL | Title | Notes |
|-------|-----|-------|-------|
| Part 1 | https://www.youtube.com/watch?v=VHcgnRl2xPM | Bitter Rivals: Iran and Saudi Arabia, Part One | Historical context |
| Part 2 | https://www.youtube.com/watch?v=PvKoniTXWsQ | Bitter Rivals: Iran and Saudi Arabia, Part Two | Modern conflicts |

## 🌐 **Various Channels + Same Topic**

### Cross-Channel Series 1: Skywatcher/UFO Investigation
**Channels:** Multiple  
**Topic:** UFO/UAP investigation, technology startups  
**Testing Purpose:** Cross-channel entity resolution, topic consistency  

| Video | URL | Title | Channel/Source | Notes |
|-------|-----|-------|----------------|-------|
| Part 1 | https://www.youtube.com/watch?v=PcuxnqQLuAQ | Skywatcher Part I: The Journey Begins | Channel A | Documentary style |
| Part 2 | https://www.youtube.com/watch?v=JUthXIGUsq8 | Skywatcher Part II: "Mapping The Unknown" | Channel B | Continuation |
| Interview | https://www.youtube.com/watch?v=y_8IKKcTntQ&t=1532s | Meet The Startup Summoning UFOs: Skywatcher Interview | Channel C | Interview format |

## 📚 **Playlist Collections (Same Channel + Various Topics)**

### Playlist Set 1: General Mixed Content
**Testing Purpose:** Topic diversity analysis, playlist processing, content categorization  

| Playlist | URL | Description | Testing Focus |
|----------|-----|-------------|---------------|
| Collection 1 | https://www.youtube.com/playlist?list=PLRJNAhZxtqH-5fKCVkZ3NLHQO3n4sLxd7 | Mixed topics | Topic detection |
| Collection 2 | https://www.youtube.com/playlist?list=PLphcdvnT8lOsNABbTl8wroFTEWubzbaWM | Mixed topics | Content variety |
| Collection 3 | https://www.youtube.com/playlist?list=PLZxP2pdh77oU5ve5Z_0iOqgf975AkhP5b | Mixed topics | Analysis depth |
| Collection 4 | https://www.youtube.com/playlist?list=PLqAK3GwrxaV-EfKnX2Cl1fj1hoJZb6ZVU | Mixed topics | Processing efficiency |
| Collection 5 | https://www.youtube.com/playlist?list=PLoW1SIeAWaWaWbHc2Vii_PA4b4lyYfu3d | Mixed topics | Scaling tests |

### Playlist Set 2: Event/Panel Collections
**Testing Purpose:** Multi-speaker events, panel discussions, speaker identification  

| Playlist | URL | Description | Testing Focus |
|----------|-----|-------------|---------------|
| Panel Event 1 | https://www.youtube.com/playlist?list=PLn5MTSAqaf8pkToANgqsSSdafXNRPDBrH | Panel with guest speakers | Speaker tracking, conversation flow |

## 🎯 **Testing Categories & Use Cases**

### Primary Testing Scenarios:
1. **Series Detection** - Videos 1-3 from Series section
2. **Entity Resolution** - Cross-channel Skywatcher series  
3. **Timeline Extraction** - Iran-Saudi Arabia or Pegasus series
4. **Multi-speaker Analysis** - Panel event playlist
5. **Topic Evolution** - Any mixed-topic playlist
6. **Narrative Flow** - My Chemical Romance series
7. **Investigative Journalism** - Pegasus or Iran-Saudi series

### Recommended Test Progression:
1. **Single Video**: Start with one Pegasus episode
2. **Simple Series**: My Chemical Romance (4 videos, clear narrative)
3. **Complex Series**: Iran-Saudi Arabia (geopolitical, timeline-heavy)
4. **Cross-Channel**: Skywatcher series (entity resolution challenge)
5. **Playlist Processing**: Start with smaller collections first

## 📝 **Notes for Development**

- **Always test with fresh data** after clearing old output
- **Pegasus videos** are excellent for timeline extraction testing
- **My Chemical Romance series** good for narrative flow
- **Panel playlists** ideal for multi-speaker analysis
- **Mixed playlists** test topic categorization and content diversity

---

*This table should be updated whenever new test videos are identified or testing requirements change.* 