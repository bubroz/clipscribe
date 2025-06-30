"""
Content Date Extractor - Fixes the Wrong Date Crisis

This module addresses the critical flaw where 90% of timeline events showed wrong dates
(video publish date 2023 instead of actual event dates 2018-2021).

PROBLEM FIXED:
- Timeline events using video.metadata.published_at + timedelta(seconds=key_point.timestamp)
- Adding video timestamp seconds as DAYS to publication date
- Results in meaningless sequential dates (2025-06-03, 2025-06-04, etc.)

SOLUTION:
- Extract dates from transcript/content ONLY
- NEVER use video publish date as fallback
- Better to have no date than wrong date
- Use chapter context for better temporal parsing
"""

import logging
import re
from datetime import datetime, timedelta
from typing import Optional, List, Dict, Any
import dateparser

from .models import ExtractedDate, DatePrecision, ChapterSegment

logger = logging.getLogger(__name__)


class ContentDateExtractor:
    """
    Extract dates from content ONLY - never from video metadata.
    
    CRITICAL RULE: NEVER return video publish date as fallback!
    Better to have no date than wrong date.
    """
    
    def __init__(self):
        """Initialize the content date extractor."""
        # Common temporal expressions to look for
        self.temporal_patterns = [
            # Specific dates
            r'\b(?:January|February|March|April|May|June|July|August|September|October|November|December)\s+\d{1,2},?\s+\d{4}\b',
            r'\b\d{1,2}[-/]\d{1,2}[-/]\d{2,4}\b',
            r'\b\d{4}[-/]\d{1,2}[-/]\d{1,2}\b',
            
            # Year references
            r'\bin\s+\d{4}\b',
            r'\bduring\s+\d{4}\b',
            r'\bback\s+in\s+\d{4}\b',
            
            # Relative dates
            r'\b(?:last|this|next)\s+(?:week|month|year|Tuesday|Wednesday|Thursday|Friday|Saturday|Sunday|Monday)\b',
            r'\b\d+\s+(?:days?|weeks?|months?|years?)\s+ago\b',
            r'\b(?:yesterday|today|tomorrow)\b',
            
            # Historical periods
            r'\bin\s+the\s+(?:early|mid|late)\s+\d{4}s?\b',
            r'\bin\s+(?:early|mid|late)\s+\d{4}\b',
        ]
        
        # Compile patterns for efficiency
        self.compiled_patterns = [re.compile(pattern, re.IGNORECASE) for pattern in self.temporal_patterns]
        
    def extract_date_from_content(self, 
                                 text: str, 
                                 chapter_context: Optional[ChapterSegment] = None,
                                 video_title: Optional[str] = None) -> Optional[ExtractedDate]:
        """
        Extract date from transcript content with chapter context.
        
        CRITICAL RULE: NEVER return video publish date as fallback!
        
        Args:
            text: The text content to extract date from
            chapter_context: Optional chapter information for context
            video_title: Optional video title for additional context
            
        Returns:
            ExtractedDate if found, None if no valid date extracted
        """
        logger.debug(f"Extracting date from content: {text[:100]}...")
        
        # Build context text with chapter information
        context_text = text
        if chapter_context:
            context_text = f"{chapter_context.title}: {text}"
            logger.debug(f"Using chapter context: {chapter_context.title}")
        
        # Find all temporal expressions in the text
        temporal_expressions = self._find_temporal_expressions(context_text)
        
        if not temporal_expressions:
            logger.debug("No temporal expressions found in content")
            return None
        
        logger.debug(f"Found {len(temporal_expressions)} temporal expressions")
        
        # Try to parse each expression, prioritizing the most specific
        for expr in temporal_expressions:
            extracted_date = self._parse_temporal_expression(
                expr.text, 
                expr.context,
                chapter_context,
                video_title
            )
            
            if extracted_date and self._is_reasonable_date(extracted_date.date):
                logger.info(f"✅ Successfully extracted date: {extracted_date.date} from '{expr.text}'")
                return extracted_date
        
        logger.debug("No valid dates could be parsed from temporal expressions")
        # CRITICAL: Never return video publish date!
        return None
    
    def _find_temporal_expressions(self, text: str) -> List[Dict[str, Any]]:
        """Find all temporal expressions in text with context."""
        expressions = []
        
        for pattern in self.compiled_patterns:
            for match in pattern.finditer(text):
                # Get surrounding context (20 chars before and after)
                start_pos = max(0, match.start() - 20)
                end_pos = min(len(text), match.end() + 20)
                context = text[start_pos:end_pos].strip()
                
                expressions.append({
                    'text': match.group(),
                    'context': context,
                    'position': match.start(),
                    'pattern_type': self._classify_pattern(match.group())
                })
        
        # Sort by specificity (more specific dates first)
        expressions.sort(key=lambda x: self._get_specificity_score(x['pattern_type']), reverse=True)
        
        return expressions
    
    def _parse_temporal_expression(self, 
                                  expr_text: str, 
                                  context: str,
                                  chapter_context: Optional[ChapterSegment] = None,
                                  video_title: Optional[str] = None) -> Optional[ExtractedDate]:
        """Parse a temporal expression into an ExtractedDate."""
        
        logger.debug(f"Parsing temporal expression: '{expr_text}' in context: '{context}'")
        
        # Use dateparser with strict settings
        parsed_date = dateparser.parse(
            expr_text,
            settings={
                'STRICT_PARSING': True,          # No fuzzy parsing
                'RETURN_AS_TIMEZONE_AWARE': False,
                'PREFER_DAY_OF_MONTH': 'first',  # Default to start of period
                'PREFER_DATES_FROM': 'past',     # Prefer past dates for historical content
                'RELATIVE_BASE': datetime.now(), # Base for relative dates
            }
        )
        
        if not parsed_date:
            logger.debug(f"dateparser could not parse: '{expr_text}'")
            return None
        
        # Determine precision and confidence
        precision = self._determine_precision(expr_text)
        confidence = self._calculate_confidence(expr_text, parsed_date, context)
        
        # Determine extraction method
        method = "dateparser_with_chapter_context" if chapter_context else "dateparser_content_only"
        
        return ExtractedDate(
            date=parsed_date,
            original_text=expr_text,
            confidence=confidence,
            source="transcript_content",
            extraction_method=method,
            chapter_context=chapter_context.title if chapter_context else None
        )
    
    def _is_reasonable_date(self, date: datetime) -> bool:
        """
        Validate that extracted date makes sense.
        
        This prevents obviously wrong dates from being returned.
        """
        now = datetime.now()
        
        # Reject dates from distant future (more than 1 year ahead)
        if date > now + timedelta(days=365):
            logger.debug(f"Rejected future date: {date}")
            return False
        
        # Reject dates from too far past (before 1900)
        if date < datetime(1900, 1, 1):
            logger.debug(f"Rejected ancient date: {date}")
            return False
        
        # Reject dates that are clearly video processing dates (today's date)
        if abs((date - now).days) < 1:
            logger.debug(f"Rejected processing date: {date}")
            return False
            
        return True
    
    def _classify_pattern(self, text: str) -> str:
        """Classify the type of temporal pattern found."""
        text_lower = text.lower()
        
        if re.match(r'\d{4}', text):
            return 'year_only'
        elif re.match(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text):
            return 'full_date'
        elif any(month in text_lower for month in ['january', 'february', 'march', 'april', 'may', 'june',
                                                   'july', 'august', 'september', 'october', 'november', 'december']):
            return 'month_year'
        elif 'ago' in text_lower:
            return 'relative_past'
        elif any(word in text_lower for word in ['yesterday', 'today', 'tomorrow']):
            return 'relative_day'
        elif 'last' in text_lower or 'next' in text_lower:
            return 'relative_period'
        else:
            return 'general'
    
    def _get_specificity_score(self, pattern_type: str) -> int:
        """Get specificity score for prioritizing patterns."""
        scores = {
            'full_date': 10,
            'month_year': 8,
            'year_only': 6,
            'relative_day': 5,
            'relative_past': 4,
            'relative_period': 3,
            'general': 1
        }
        return scores.get(pattern_type, 0)
    
    def _determine_precision(self, expr_text: str) -> DatePrecision:
        """Determine the precision level of the extracted date."""
        text_lower = expr_text.lower()
        
        if re.search(r'\d{1,2}:\d{2}', text_lower):
            return DatePrecision.EXACT
        elif re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{2,4}', text_lower):
            return DatePrecision.DAY
        elif any(month in text_lower for month in ['january', 'february', 'march', 'april', 'may', 'june',
                                                   'july', 'august', 'september', 'october', 'november', 'december']):
            return DatePrecision.MONTH
        elif re.search(r'\b\d{4}\b', text_lower):
            return DatePrecision.YEAR
        else:
            return DatePrecision.APPROXIMATE
    
    def _calculate_confidence(self, expr_text: str, parsed_date: datetime, context: str) -> float:
        """Calculate confidence score for the extracted date."""
        confidence = 0.5  # Base confidence
        
        # Boost for specific date patterns
        if re.search(r'\d{1,2}[-/]\d{1,2}[-/]\d{4}', expr_text):
            confidence += 0.3
        elif re.search(r'\b\d{4}\b', expr_text):
            confidence += 0.2
        
        # Boost for context clues
        context_lower = context.lower()
        if any(word in context_lower for word in ['on', 'in', 'during', 'happened', 'occurred']):
            confidence += 0.1
        
        # Penalty for vague expressions
        if any(word in expr_text.lower() for word in ['around', 'approximately', 'about']):
            confidence -= 0.1
        
        # Boost for reasonable historical dates
        years_ago = (datetime.now() - parsed_date).days / 365
        if 1 <= years_ago <= 50:  # Reasonable historical range
            confidence += 0.1
        
        return min(1.0, max(0.0, confidence))
    
    def extract_multiple_dates(self, text: str, chapter_context: Optional[ChapterSegment] = None) -> List[ExtractedDate]:
        """Extract multiple dates from content, sorted by confidence."""
        all_expressions = self._find_temporal_expressions(text)
        extracted_dates = []
        
        for expr in all_expressions:
            extracted_date = self._parse_temporal_expression(
                expr['text'],
                expr['context'],
                chapter_context
            )
            
            if extracted_date and self._is_reasonable_date(extracted_date.date):
                extracted_dates.append(extracted_date)
        
        # Sort by confidence (highest first)
        extracted_dates.sort(key=lambda x: x.confidence, reverse=True)
        
        # Remove duplicates (same date)
        unique_dates = []
        seen_dates = set()
        
        for date_obj in extracted_dates:
            date_key = date_obj.date.strftime('%Y-%m-%d')
            if date_key not in seen_dates:
                unique_dates.append(date_obj)
                seen_dates.add(date_key)
        
        logger.info(f"Extracted {len(unique_dates)} unique dates from content")
        return unique_dates 