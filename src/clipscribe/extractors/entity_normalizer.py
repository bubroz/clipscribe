"""
Entity Normalizer for ClipScribe.

Handles entity deduplication, normalization, and resolution across multiple extraction methods.
Ensures clean, consistent entities for network analysis 
"""

import logging
from typing import List, Dict, Tuple, Optional
try:
    from typing import Set
except ImportError:
    from collections.abc import Set
from collections import defaultdict
import re
from difflib import SequenceMatcher

from ..models import Entity

logger = logging.getLogger(__name__)


class EntityNormalizer:
    """
    Normalizes and deduplicates entities across extraction methods.
    
    Features:
    - Cross-method deduplication (SpaCy + GLiNER + REBEL)
    - Entity name normalization (Trump = Donald Trump = President Trump)
    - Type consistency enforcement
    - Alias resolution
    - Confidence-based merging
    """
    
    def __init__(self, similarity_threshold: float = 0.85):
        """
        Initialize entity normalizer.
        
        Args:
            similarity_threshold: Minimum similarity to consider entities the same
        """
        self.similarity_threshold = similarity_threshold
        
        # Common title patterns for people
        self.person_titles = {
            'president', 'vice president', 'senator', 'congressman', 'congresswoman',
            'governor', 'mayor', 'judge', 'justice', 'secretary', 'minister',
            'prime minister', 'chancellor', 'ambassador', 'general', 'admiral',
            'colonel', 'captain', 'lieutenant', 'dr', 'doctor', 'professor',
            'ceo', 'cto', 'cfo', 'chairman', 'director', 'manager'
        }
        
        # Common organization suffixes
        self.org_suffixes = {
            'inc', 'corp', 'corporation', 'company', 'co', 'ltd', 'limited',
            'llc', 'llp', 'lp', 'plc', 'ag', 'sa', 'gmbh', 'foundation',
            'institute', 'university', 'college', 'school', 'hospital',
            'department', 'agency', 'bureau', 'commission', 'authority'
        }
        
    def normalize_entities(self, entities: List[Entity]) -> List[Entity]:
        """
        Normalize and deduplicate a list of entities.
        
        Args:
            entities: Raw entities from all extraction methods
            
        Returns:
            Cleaned, normalized, and deduplicated entities
        """
        if not entities:
            return []
            
        logger.info(f"Normalizing {len(entities)} entities...")
        logger.debug(f"DEBUG: Input entities: {[e.entity for e in entities[:10]]}...")  # Show first 10
        
        # Step 1: Basic cleanup
        cleaned_entities = self._clean_entity_names(entities)
        logger.debug(f"DEBUG: After cleanup: {len(cleaned_entities)} entities")
        
        # Step 2: Group similar entities
        entity_groups = self._group_similar_entities(cleaned_entities)
        logger.debug(f"DEBUG: Grouped into {len(entity_groups)} groups")
        
        # Step 3: Merge each group into a single canonical entity
        normalized_entities = []
        for group in entity_groups:
            canonical = self._merge_entity_group(group)
            if canonical:
                normalized_entities.append(canonical)
        logger.debug(f"DEBUG: After merging groups: {len(normalized_entities)} entities")
        
        # Step 4: Final validation and sorting
        final_entities = self._validate_and_sort(normalized_entities)
        logger.debug(f"DEBUG: After validation: {len(final_entities)} entities")
        
        logger.info(f"Normalized to {len(final_entities)} unique entities ")
        return final_entities
        
    def _clean_entity_names(self, entities: List[Entity]) -> List[Entity]:
        """Clean and standardize entity names."""
        cleaned = []
        
        for entity in entities:
            # Skip empty or very short names
            if not entity.entity or len(entity.entity.strip()) < 2:
                continue
                
            # Clean the name
            clean_name = self._clean_name(entity.entity)
            if not clean_name:
                continue
                
            # Create cleaned entity
            cleaned_entity = Entity(
                entity=clean_name,
                type=entity.type.upper(),  # Standardize type case
                source=entity.source
            )
            cleaned.append(cleaned_entity)
            
        return cleaned
        
    def _clean_name(self, name: str) -> str:
        """Clean an individual entity name."""
        # Remove extra whitespace
        name = re.sub(r'\s+', ' ', name.strip())
        
        # Remove quotes and brackets
        name = re.sub(r'^["\'\[\(]+|["\'\]\)]+$', '', name)
        
        # Remove trailing punctuation (but keep periods in abbreviations)
        name = re.sub(r'[,;:!?]+$', '', name)
        
        # Fix common OCR/transcription errors
        name = re.sub(r'\b([A-Z])\s+([A-Z])\b', r'\1\2', name)  # "U S A" -> "USA"
        
        # Capitalize properly
        if name.isupper() or name.islower():
            # If all caps or all lowercase, title case it
            name = name.title()
            
        return name.strip()
        
    def _group_similar_entities(self, entities: List[Entity]) -> List[List[Entity]]:
        """Group entities that likely refer to the same thing."""
        groups = []
        used = set()
        
        for i, entity in enumerate(entities):
            if i in used:
                continue
                
            # Start a new group with this entity
            group = [entity]
            used.add(i)
            
            # Find similar entities
            for j, other_entity in enumerate(entities[i+1:], i+1):
                if j in used:
                    continue
                    
                if self._are_same_entity(entity, other_entity):
                    group.append(other_entity)
                    used.add(j)
                    
            groups.append(group)
            
        return groups
        
    def _are_same_entity(self, entity1: Entity, entity2: Entity) -> bool:
        """Determine if two entities refer to the same thing."""
        # Must be same type (with some flexibility)
        if not self._compatible_types(entity1.type, entity2.type):
            return False
            
        # Check name similarity
        return self._similar_names(entity1.entity, entity2.entity)
        
    def _compatible_types(self, type1: str, type2: str) -> bool:
        """Check if two entity types are compatible using hierarchical mapping."""
        type1, type2 = type1.upper(), type2.upper()
        
        # Exact match
        if type1 == type2:
            return True
            
        # Enhanced hierarchical entity type system for intelligence analysis
        entity_hierarchy = {
            # Core NER compatibility
            'PERSON': {
                'aliases': {'PER', 'PERSON'},
                'subtypes': {
                    # Military Personnel (detailed breakdown)
                    'ENLISTED_PERSONNEL': {'E1', 'E2', 'E3', 'E4', 'E5', 'E6', 'E7', 'E8', 'E9', 'ENLISTED', 'SOLDIER', 'MARINE', 'SAILOR', 'AIRMAN'},
                    'NON_COMMISSIONED_OFFICER': {'NCO', 'SERGEANT', 'CORPORAL', 'STAFF_SERGEANT', 'SERGEANT_MAJOR'},
                    'WARRANT_OFFICER': {'WO1', 'WO2', 'WO3', 'WO4', 'WO5', 'WARRANT_OFFICER', 'CHIEF_WARRANT_OFFICER'},
                    'COMMISSIONED_OFFICER': {'LIEUTENANT', 'CAPTAIN', 'MAJOR', 'COLONEL', 'GENERAL', 'ADMIRAL', 'COMMANDER', 'OFFICER'},
                    
                    # Political & Government Personnel
                    'POLITICAL_FIGURE': {'POLITICIAN', 'PRESIDENT', 'PRIME_MINISTER', 'SENATOR', 'CONGRESSMAN', 'GOVERNOR', 'MAYOR'},
                    'GOVERNMENT_OFFICIAL': {'SECRETARY', 'MINISTER', 'AMBASSADOR', 'DIPLOMAT', 'CIVIL_SERVANT', 'BUREAUCRAT'},
                    'INTELLIGENCE_OFFICER': {'CIA_OFFICER', 'FBI_AGENT', 'NSA_ANALYST', 'SPY', 'OPERATIVE', 'HANDLER'},
                    
                    # Criminal & Threat Actors
                    'CRIMINAL': {'SUSPECT', 'DEFENDANT', 'CONVICT', 'GANG_MEMBER', 'CARTEL_MEMBER', 'MOBSTER'},
                    'TERRORIST': {'JIHADIST', 'EXTREMIST', 'MILITANT', 'INSURGENT', 'BOMBER', 'CELL_MEMBER'},
                    'THREAT_ACTOR': {'HACKER', 'CYBER_CRIMINAL', 'APT_ACTOR', 'STATE_ACTOR', 'INSIDER_THREAT'},
                    
                    # Business & Economic
                    'BUSINESS_EXECUTIVE': {'CEO', 'CFO', 'CTO', 'CHAIRMAN', 'BOARD_MEMBER', 'EXECUTIVE'},
                    'ENTREPRENEUR': {'FOUNDER', 'STARTUP_FOUNDER', 'INVESTOR', 'VENTURE_CAPITALIST'},
                    'FINANCIAL_ACTOR': {'TRADER', 'BANKER', 'ANALYST', 'FUND_MANAGER', 'BROKER'},
                    
                    # Religious & Ideological
                    'RELIGIOUS_FIGURE': {'PRIEST', 'IMAM', 'RABBI', 'MONK', 'CLERIC', 'RELIGIOUS_LEADER'},
                    'IDEOLOGICAL_LEADER': {'ACTIVIST', 'DISSIDENT', 'REVOLUTIONARY', 'PROPAGANDIST'},
                    
                    # Modern Relationships & Social
                    'INFLUENCER': {'SOCIAL_MEDIA_INFLUENCER', 'BLOGGER', 'YOUTUBER', 'TIKTOKER'},
                    'RELATIONSHIP_CONTACT': {'SPOUSE', 'PARTNER', 'ASSOCIATE', 'COLLEAGUE', 'CONTACT'}
                }
            },
            
            'ORGANIZATION': {
                'aliases': {'ORG', 'ORGANIZATION', 'COMPANY'},
                'subtypes': {
                    # Military & Defense
                    'MILITARY_UNIT': {'BRIGADE', 'BATTALION', 'REGIMENT', 'SQUADRON', 'PLATOON', 'COMPANY_MILITARY'},
                    'DEFENSE_CONTRACTOR': {'DEFENSE_COMPANY', 'ARMS_MANUFACTURER', 'MILITARY_SUPPLIER'},
                    'INTELLIGENCE_AGENCY': {'CIA', 'NSA', 'FBI', 'DIA', 'MOSSAD', 'MI6', 'SVR', 'MSS'},
                    
                    # Government & Political
                    'GOVERNMENT_AGENCY': {'DEPARTMENT', 'MINISTRY', 'BUREAU', 'COMMISSION', 'AUTHORITY'},
                    'POLITICAL_PARTY': {'PARTY', 'POLITICAL_MOVEMENT', 'COALITION', 'FACTION'},
                    'DIPLOMATIC_MISSION': {'EMBASSY', 'CONSULATE', 'MISSION', 'DELEGATION'},
                    
                    # Criminal & Terrorist Organizations
                    'CRIMINAL_ORGANIZATION': {'CARTEL', 'MAFIA', 'GANG', 'CRIME_FAMILY', 'SYNDICATE'},
                    'TERRORIST_ORGANIZATION': {'TERROR_GROUP', 'MILITANT_GROUP', 'INSURGENCY', 'CELL'},
                    'APT_GROUP': {'CYBER_GROUP', 'HACKER_GROUP', 'STATE_SPONSORED_GROUP'},
                    
                    # Business & Economic
                    'CORPORATION': {'COMPANY', 'FIRM', 'ENTERPRISE', 'BUSINESS', 'STARTUP'},
                    'FINANCIAL_INSTITUTION': {'BANK', 'FUND', 'INVESTMENT_FIRM', 'HEDGE_FUND'},
                    'TECH_COMPANY': {'SOFTWARE_COMPANY', 'HARDWARE_COMPANY', 'AI_COMPANY'},
                    
                    # Energy & Infrastructure
                    'ENERGY_COMPANY': {'OIL_COMPANY', 'GAS_COMPANY', 'UTILITY', 'RENEWABLE_COMPANY'},
                    'INFRASTRUCTURE_OPERATOR': {'TELECOM', 'TRANSPORTATION_COMPANY', 'LOGISTICS_COMPANY'},
                    
                    # Religious & Ideological
                    'RELIGIOUS_ORGANIZATION': {'CHURCH', 'MOSQUE', 'SYNAGOGUE', 'TEMPLE', 'RELIGIOUS_GROUP'},
                    'IDEOLOGICAL_GROUP': {'THINK_TANK', 'ADVOCACY_GROUP', 'MOVEMENT', 'NGO'},
                    
                    # Media & Information
                    'MEDIA_ORGANIZATION': {'NEWS_OUTLET', 'BROADCASTER', 'PUBLISHER', 'SOCIAL_MEDIA_PLATFORM'},
                    'INFORMATION_OPERATION': {'PROPAGANDA_OUTLET', 'DISINFORMATION_GROUP', 'INFLUENCE_NETWORK'}
                }
            },
            
            'LOCATION': {
                'aliases': {'LOC', 'LOCATION', 'GPE', 'PLACE', 'GEOPOLITICAL_ENTITY'},
                'subtypes': {
                    # Military & Strategic Locations
                    'MILITARY_BASE': {'BASE', 'INSTALLATION', 'GARRISON', 'NAVAL_BASE', 'AIR_BASE'},
                    'STRATEGIC_LOCATION': {'CHOKEPOINT', 'STRAIT', 'PASSAGE', 'BORDER_CROSSING'},
                    'CONFLICT_ZONE': {'BATTLEFIELD', 'WAR_ZONE', 'COMBAT_AREA', 'FRONT_LINE'},
                    
                    # Critical Infrastructure
                    'ENERGY_FACILITY': {'POWER_PLANT', 'REFINERY', 'PIPELINE', 'DRILLING_SITE', 'SOLAR_FARM'},
                    'TRANSPORTATION_HUB': {'AIRPORT', 'PORT', 'RAILWAY_STATION', 'LOGISTICS_CENTER'},
                    'CYBER_INFRASTRUCTURE': {'DATA_CENTER', 'SERVER_FARM', 'TELECOM_FACILITY'},
                    
                    # Political & Administrative
                    'GOVERNMENT_FACILITY': {'CAPITOL', 'PARLIAMENT', 'MINISTRY_BUILDING', 'COURTHOUSE'},
                    'DIPLOMATIC_FACILITY': {'EMBASSY_BUILDING', 'CONSULATE_BUILDING', 'DIPLOMATIC_COMPOUND'},
                    
                    # Criminal & Security Concerns
                    'CRIME_SCENE': {'INCIDENT_LOCATION', 'ATTACK_SITE', 'BOMBING_SITE'},
                    'DETENTION_FACILITY': {'PRISON', 'JAIL', 'DETENTION_CENTER', 'BLACK_SITE'},
                    'SAFE_HOUSE': {'HIDEOUT', 'COMPOUND', 'SANCTUARY'},
                    
                    # Economic & Business
                    'FINANCIAL_CENTER': {'STOCK_EXCHANGE', 'BANKING_DISTRICT', 'FINANCIAL_HUB'},
                    'COMMERCIAL_FACILITY': {'SHOPPING_CENTER', 'MARKET', 'TRADE_CENTER'},
                    'MANUFACTURING_SITE': {'FACTORY', 'PLANT', 'FACILITY', 'PRODUCTION_CENTER'},
                    
                    # Religious & Cultural
                    'RELIGIOUS_SITE': {'MOSQUE', 'CHURCH', 'TEMPLE', 'SHRINE', 'HOLY_SITE'},
                    'CULTURAL_SITE': {'MONUMENT', 'HERITAGE_SITE', 'CULTURAL_CENTER'}
                }
            },
            
            'EVENT': {
                'aliases': {'EVENT', 'INCIDENT', 'OPERATION', 'CONFLICT'},
                'subtypes': {
                    # Military Operations & Conflicts
                    'MILITARY_OPERATION': {'COMBAT_OPERATION', 'PEACEKEEPING_MISSION', 'EXERCISE', 'DEPLOYMENT'},
                    'ACT_OF_WAR': {'INVASION', 'BOMBING', 'MISSILE_STRIKE', 'NAVAL_BATTLE', 'AIR_STRIKE'},
                    'CYBER_OPERATION': {'CYBER_ATTACK', 'HACK', 'DATA_BREACH', 'CYBER_ESPIONAGE'},
                    
                    # Criminal & Terrorist Activities
                    'TERRORIST_ATTACK': {'BOMBING', 'SHOOTING', 'VEHICLE_ATTACK', 'SUICIDE_BOMBING'},
                    'CRIMINAL_ACTIVITY': {'ROBBERY', 'KIDNAPPING', 'ASSASSINATION', 'DRUG_TRAFFICKING'},
                    'CORRUPTION_SCANDAL': {'BRIBERY', 'EMBEZZLEMENT', 'KICKBACK', 'FRAUD'},
                    
                    # Political Events
                    'POLITICAL_EVENT': {'ELECTION', 'SUMMIT', 'NEGOTIATION', 'TREATY_SIGNING'},
                    'POLITICAL_SCANDAL': {'SCANDAL', 'CONTROVERSY', 'LEAK', 'COVER_UP'},
                    'INFORMATION_CAMPAIGN': {'PROPAGANDA_CAMPAIGN', 'DISINFORMATION_CAMPAIGN', 'INFLUENCE_OPERATION'},
                    
                    # Economic & Business Events
                    'ECONOMIC_EVENT': {'MARKET_CRASH', 'RECESSION', 'SANCTIONS', 'TRADE_WAR'},
                    'BUSINESS_EVENT': {'MERGER', 'ACQUISITION', 'IPO', 'BANKRUPTCY', 'PRODUCT_LAUNCH'},
                    
                    # Social & Cultural Events
                    'SOCIAL_MOVEMENT': {'PROTEST', 'DEMONSTRATION', 'UPRISING', 'REVOLUTION'},
                    'RELIGIOUS_EVENT': {'PILGRIMAGE', 'RELIGIOUS_FESTIVAL', 'CEREMONY'},
                    
                    # Natural & Man-made Disasters
                    'DISASTER': {'EARTHQUAKE', 'HURRICANE', 'FLOOD', 'WILDFIRE', 'PANDEMIC'},
                    'ACCIDENT': {'PLANE_CRASH', 'INDUSTRIAL_ACCIDENT', 'TRANSPORTATION_ACCIDENT'}
                }
            },
            
            'TECHNOLOGY': {
                'aliases': {'TECH', 'TECHNOLOGY', 'SYSTEM', 'PLATFORM'},
                'subtypes': {
                    # Military Technology
                    'WEAPON_SYSTEM': {'MISSILE', 'AIRCRAFT', 'TANK', 'SHIP', 'SUBMARINE', 'DRONE'},
                    'DEFENSE_TECHNOLOGY': {'RADAR', 'SONAR', 'COMMUNICATION_SYSTEM', 'SURVEILLANCE_SYSTEM'},
                    'MILITARY_PLATFORM': {'FIGHTER_JET', 'BOMBER', 'HELICOPTER', 'WARSHIP', 'ARMORED_VEHICLE'},
                    
                    # Advanced Technologies
                    'AI_SYSTEM': {'MACHINE_LEARNING', 'NEURAL_NETWORK', 'CHATBOT', 'AI_MODEL'},
                    'QUANTUM_TECHNOLOGY': {'QUANTUM_COMPUTER', 'QUANTUM_ENCRYPTION', 'QUANTUM_SENSOR'},
                    'BIOTECHNOLOGY': {'GENE_THERAPY', 'CRISPR', 'SYNTHETIC_BIOLOGY', 'BIOWEAPON'},
                    'SEMICONDUCTOR': {'MICROCHIP', 'PROCESSOR', 'INTEGRATED_CIRCUIT', 'MEMORY_CHIP'},
                    
                    # Cyber & Information Technology
                    'SOFTWARE': {'APPLICATION', 'OPERATING_SYSTEM', 'DATABASE', 'MALWARE'},
                    'NETWORK_TECHNOLOGY': {'INTERNET', 'SATELLITE', 'FIBER_OPTIC', '5G'},
                    'SURVEILLANCE_TECH': {'FACIAL_RECOGNITION', 'BIOMETRIC', 'TRACKING_SYSTEM'},
                    
                    # Energy Technology
                    'ENERGY_TECHNOLOGY': {'SOLAR_PANEL', 'WIND_TURBINE', 'NUCLEAR_REACTOR', 'BATTERY'}
                }
            },
            
            'RESOURCE': {
                'aliases': {'RESOURCE', 'COMMODITY', 'ASSET', 'MATERIAL'},
                'subtypes': {
                    # Strategic Resources
                    'ENERGY_RESOURCE': {'OIL', 'NATURAL_GAS', 'COAL', 'URANIUM', 'LITHIUM'},
                    'STRATEGIC_MINERAL': {'RARE_EARTH', 'COBALT', 'GRAPHITE', 'TITANIUM', 'PLATINUM'},
                    'AGRICULTURAL_RESOURCE': {'WHEAT', 'RICE', 'CORN', 'SOYBEANS', 'FERTILIZER'},
                    
                    # Financial Resources
                    'FINANCIAL_INSTRUMENT': {'BOND', 'STOCK', 'DERIVATIVE', 'CRYPTOCURRENCY'},
                    'CURRENCY': {'DOLLAR', 'EURO', 'YEN', 'YUAN', 'BITCOIN'},
                    
                    # Information Resources
                    'INTELLIGENCE': {'CLASSIFIED_DOCUMENT', 'INTEL_REPORT', 'SURVEILLANCE_DATA'},
                    'DATA': {'PERSONAL_DATA', 'FINANCIAL_DATA', 'BIOMETRIC_DATA', 'METADATA'}
                }
            },
            
            'CONCEPT': {
                'aliases': {'CONCEPT', 'DOCTRINE', 'STRATEGY', 'POLICY'},
                'subtypes': {
                    # Military & Security Concepts
                    'MILITARY_DOCTRINE': {'STRATEGY', 'TACTIC', 'PROCEDURE', 'PROTOCOL'},
                    'SECURITY_CONCEPT': {'THREAT_MODEL', 'RISK_ASSESSMENT', 'VULNERABILITY'},
                    
                    # Political & Ideological Concepts
                    'POLITICAL_IDEOLOGY': {'DEMOCRACY', 'AUTHORITARIANISM', 'SOCIALISM', 'NATIONALISM'},
                    'GEOPOLITICAL_CONCEPT': {'SPHERE_OF_INFLUENCE', 'BALANCE_OF_POWER', 'CONTAINMENT'},
                    
                    # Religious & Cultural Concepts
                    'RELIGIOUS_BELIEF': {'ISLAM', 'CHRISTIANITY', 'JUDAISM', 'BUDDHISM', 'SECULARISM'},
                    'CULTURAL_CONCEPT': {'TRADITION', 'CUSTOM', 'NORM', 'VALUE_SYSTEM'},
                    
                    # Economic Concepts
                    'ECONOMIC_THEORY': {'CAPITALISM', 'SOCIALISM', 'FREE_MARKET', 'PROTECTIONISM'},
                    'BUSINESS_CONCEPT': {'SUPPLY_CHAIN', 'LOGISTICS', 'MARKET_SHARE', 'COMPETITIVE_ADVANTAGE'}
                }
            },
            
            # Time-related entities
            'TIME': {
                'aliases': {'DATE', 'TIME', 'TEMPORAL'},
                'subtypes': {
                    'HISTORICAL_PERIOD': {'COLD_WAR', 'POST_9_11', 'ARAB_SPRING'},
                    'OPERATIONAL_TIMEFRAME': {'DEPLOYMENT_PERIOD', 'MISSION_DURATION'}
                }
            },
            
            # Quantity and measurement entities
            'QUANTITY': {
                'aliases': {'MONEY', 'FINANCIAL_METRIC', 'PERCENTAGE', 'NUMBER', 'MEASUREMENT'},
                'subtypes': {
                    'MILITARY_METRIC': {'TROOP_STRENGTH', 'CASUALTY_COUNT', 'EQUIPMENT_COUNT'},
                    'ECONOMIC_METRIC': {'GDP', 'BUDGET', 'TRADE_VOLUME', 'MARKET_CAP'},
                    'PERFORMANCE_METRIC': {'RANGE', 'SPEED', 'PAYLOAD', 'ACCURACY'}
                }
            }
        }
        
        # Check hierarchical compatibility
        for main_type, type_data in entity_hierarchy.items():
            # Check if both types belong to the same main category
            type1_in_main = (type1 in type_data['aliases'] or 
                           any(type1 in subtypes for subtypes in type_data['subtypes'].values()))
            type2_in_main = (type2 in type_data['aliases'] or 
                           any(type2 in subtypes for subtypes in type_data['subtypes'].values()))
            
            if type1_in_main and type2_in_main:
                return True
                
        return False
        
    def _similar_names(self, name1: str, name2: str) -> bool:
        """Check if two names refer to the same entity."""
        name1_lower = name1.lower()
        name2_lower = name2.lower()
        
        # Exact match
        if name1_lower == name2_lower:
            return True
            
        # One is contained in the other (after removing titles)
        clean1 = self._remove_titles(name1_lower)
        clean2 = self._remove_titles(name2_lower)
        
        if clean1 in clean2 or clean2 in clean1:
            return True
            
        # Check for common abbreviations
        if self._check_abbreviations(clean1, clean2):
            return True
            
        # String similarity
        similarity = SequenceMatcher(None, clean1, clean2).ratio()
        return similarity >= self.similarity_threshold
        
    def _remove_titles(self, name: str) -> str:
        """Remove titles and honorifics from names."""
        words = name.split()
        filtered_words = []
        
        for word in words:
            # Remove common titles
            clean_word = word.strip('.,')
            if clean_word not in self.person_titles:
                filtered_words.append(word)
                
        return ' '.join(filtered_words).strip()
        
    def _check_abbreviations(self, name1: str, name2: str) -> bool:
        """Check for common abbreviation patterns."""
        # Check if one is an acronym of the other
        words1 = name1.split()
        words2 = name2.split()
        
        # If one is much shorter, check if it's an acronym
        if len(words1) == 1 and len(words2) > 1:
            acronym = ''.join(word[0] for word in words2 if word)
            return words1[0].replace('.', '') == acronym.lower()
        elif len(words2) == 1 and len(words1) > 1:
            acronym = ''.join(word[0] for word in words1 if word)
            return words2[0].replace('.', '') == acronym.lower()
            
        return False
        
    def _merge_entity_group(self, group: List[Entity]) -> Optional[Entity]:
        """Merge a group of similar entities into one canonical entity."""
        if not group:
            return None
            
        if len(group) == 1:
            return group[0]
            
        # Sort by entity name length (longest first)
        group.sort(key=lambda e: len(e.entity), reverse=True)
        
        # Use the entity with longest name as base
        canonical = group[0]
        
        # Choose the best name (usually the longest, most complete one)
        best_name = self._choose_best_name([e.entity for e in group])
        canonical.entity = best_name
        
        # Track sources
        sources = set()
        
        for entity in group:
            if entity.source:
                sources.add(entity.source)
                    
        # Update source to include all sources
        if sources:
            canonical.source = '+'.join(sorted(sources))
        
        return canonical
        
    def _choose_best_name(self, names: List[str]) -> str:
        """Choose the best name from a list of candidates."""
        if not names:
            return ""
            
        if len(names) == 1:
            return names[0]
            
        # Prefer longer, more complete names
        # But avoid overly long names that might be errors
        scored_names = []
        
        for name in names:
            score = 0
            
            # Length bonus (up to a point)
            length_score = min(len(name), 50) / 50.0
            score += length_score * 0.3
            
            # Word count bonus (more words usually = more complete)
            word_count = len(name.split())
            word_score = min(word_count, 5) / 5.0
            score += word_score * 0.4
            
            # Capitalization bonus (proper names should be capitalized)
            if name[0].isupper():
                score += 0.2
                
            # Penalty for all caps or all lowercase
            if name.isupper() or name.islower():
                score -= 0.1
                
            scored_names.append((score, name))
            
        # Return the highest scoring name
        scored_names.sort(reverse=True)
        return scored_names[0][1]
        
    def _validate_and_sort(self, entities: List[Entity]) -> List[Entity]:
        """Final validation and sorting of entities."""
        valid_entities = []
        
        for entity in entities:
            # Skip entities with empty names
            if not entity.entity or len(entity.entity.strip()) < 2:
                continue
                
            # Skip very short names (likely noise)
            if len(entity.entity) < 2:
                continue
                
            # Skip common stop words that got through
            if entity.entity.lower() in {'the', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for', 'of', 'with', 'by'}:
                continue
                
            valid_entities.append(entity)
            
        # Sort by name length (longer first), then alphabetically
        valid_entities.sort(key=lambda e: (-len(e.entity), e.entity.lower()))
        
        return valid_entities
        
    def get_entity_aliases(self, entities: List[Entity]) -> Dict[str, List[str]]:
        """Get a mapping of canonical names to their aliases."""
        aliases = defaultdict(list)
        
        # Group entities again to find aliases
        groups = self._group_similar_entities(entities)
        
        for group in groups:
            if len(group) > 1:
                canonical_name = self._choose_best_name([e.entity for e in group])
                for entity in group:
                    if entity.entity != canonical_name:
                        aliases[canonical_name].append(entity.entity)
                        
        return dict(aliases)
        
    def create_entity_lookup(self, entities: List[Entity]) -> Dict[str, str]:
        """Create a lookup table from any name variant to canonical name."""
        lookup = {}
        
        # Add the canonical names
        for entity in entities:
            lookup[entity.entity.lower()] = entity.entity
            
        # Add aliases
        aliases = self.get_entity_aliases(entities)
        for canonical, alias_list in aliases.items():
            for alias in alias_list:
                lookup[alias.lower()] = canonical
                
        return lookup 