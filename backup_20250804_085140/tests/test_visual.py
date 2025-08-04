#!/usr/bin/env python3
"""Test ultrathink visual analysis functionality"""

import unittest
from unittest.mock import Mock, patch
import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent.parent / 'src'))

from visual_analyzer import VisualAnalyzerAdvanced


class TestVisualAnalyzer(unittest.TestCase):
    """Test ultrathink visual analyzer"""
    
    def setUp(self):
        """Setup test fixtures"""
        self.analyzer = VisualAnalyzerAdvanced()
    
    def test_analyzer_initialization(self):
        """Test analyzer initializes correctly"""
        self.assertIsNotNone(self.analyzer)
        self.assertTrue(hasattr(self.analyzer, 'analyze_screen'))
        self.assertTrue(hasattr(self.analyzer, 'plan_task'))
    
    def test_analyze_screen(self):
        """Test screen analysis"""
        mock_screenshot = {
            'width': 1920,
            'height': 1080,
            'data': 'mock_base64_data'
        }
        
        result = self.analyzer.analyze_screen(
            mock_screenshot,
            "Find all buttons"
        )
        
        self.assertIsInstance(result, dict)
        self.assertIn('elements', result)
    
    def test_plan_task(self):
        """Test task planning"""
        task = "Click the submit button and wait for response"
        
        plan = self.analyzer.plan_task(task)
        
        self.assertIsInstance(plan, dict)
        self.assertIn('steps', plan)
        self.assertIsInstance(plan['steps'], list)
        self.assertTrue(len(plan['steps']) > 0)
    
    def test_element_detection(self):
        """Test UI element detection"""
        elements = self.analyzer.detect_elements({
            'width': 1920,
            'height': 1080,
            'data': 'mock_data'
        })
        
        self.assertIsInstance(elements, list)
    
    def test_action_validation(self):
        """Test action validation"""
        valid_action = {
            'type': 'click',
            'x': 500,
            'y': 300
        }
        
        self.assertTrue(self.analyzer.validate_action(valid_action))
        
        invalid_action = {
            'type': 'unknown',
            'data': 'test'
        }
        
        self.assertFalse(self.analyzer.validate_action(invalid_action))
    
    def test_confidence_scoring(self):
        """Test confidence scoring for actions"""
        action = {
            'type': 'click',
            'target': 'submit button',
            'context': 'form submission'
        }
        
        confidence = self.analyzer.get_confidence_score(action)
        
        self.assertIsInstance(confidence, float)
        self.assertTrue(0 <= confidence <= 1)
    
    def test_error_recovery_planning(self):
        """Test error recovery planning"""
        error_context = {
            'error': 'Element not found',
            'action': 'click',
            'target': 'button'
        }
        
        recovery_plan = self.analyzer.plan_error_recovery(error_context)
        
        self.assertIsInstance(recovery_plan, dict)
        self.assertIn('steps', recovery_plan)
    
    def test_multi_step_workflow(self):
        """Test multi-step workflow planning"""
        workflow = "Login to application, navigate to settings, enable dark mode"
        
        plan = self.analyzer.plan_workflow(workflow)
        
        self.assertIsInstance(plan, dict)
        self.assertIn('steps', plan)
        self.assertTrue(len(plan['steps']) >= 3)
    
    def test_visual_similarity_check(self):
        """Test visual similarity checking"""
        screenshot1 = {'data': 'image1'}
        screenshot2 = {'data': 'image2'}
        
        similarity = self.analyzer.check_similarity(screenshot1, screenshot2)
        
        self.assertIsInstance(similarity, float)
        self.assertTrue(0 <= similarity <= 1)
    
    def test_ocr_text_extraction(self):
        """Test OCR text extraction from screenshot"""
        screenshot = {
            'width': 1920,
            'height': 1080,
            'data': 'mock_image_with_text'
        }
        
        text = self.analyzer.extract_text(screenshot)
        
        self.assertIsInstance(text, str)


if __name__ == "__main__":
    unittest.main()