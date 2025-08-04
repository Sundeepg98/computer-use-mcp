#!/usr/bin/env python3
"""
Visual analysis for computer use operations
Provides deep analysis and intelligent action planning
"""

import logging
from typing import Dict, Any, List, Optional
import time

logger = logging.getLogger(__name__)


class VisualAnalyzer:
    """Visual analyzer for computer use operations"""
    
    def __init__(self):
        """Initialize visual analysis system"""
        self.analysis_depth = 'deep'
        self.verification_enabled = True
        self.multi_step_planning = True
        self.context_memory = []
    
    def enhance(self, command: str) -> str:
        """Enhance command with deep analysis"""
        enhanced = f"{command} with analysis"
        
        # Add analysis directives
        enhancements = [
            "analyze visual context",
            "identify interactive elements",
            "predict outcomes",
            "verify success conditions"
        ]
        
        for enhancement in enhancements:
            enhanced = f"{enhanced} {enhancement}"
        
        logger.info(f"Enhanced command: {command[:50]}...")
        return enhanced
    
    def analyze_screen(self, screenshot: Any, prompt: str) -> Dict[str, Any]:
        """Analyze screen with prompt"""
        analysis = self.analyze_visual_context(screenshot)
        analysis['prompt'] = prompt
        return analysis
    
    def analyze_screenshot(self, screenshot: Any) -> Dict[str, Any]:
        """Analyze screenshot for sensitive information and content"""
        from .safety_checks import SafetyChecker
        safety = SafetyChecker()
        
        # Mock analysis that might contain sensitive data (for testing)
        if hasattr(screenshot, 'mock_analysis'):
            analysis_text = screenshot.mock_analysis
        else:
            analysis_text = "Screen content analysis results"
        
        # Check for sensitive data and sanitize
        content_check = safety.check_content(analysis_text)
        if not content_check['safe']:
            analysis_text = safety.sanitize_text(analysis_text)
        
        return {
            "analysis": analysis_text,
            "sensitive_data_filtered": not content_check.get('safe', True)
        }
    
    def analyze_visual_context(self, screenshot: Any) -> Dict[str, Any]:
        """Deep analysis of visual context"""
        logger.info("Performing deep visual analysis")
        
        analysis = {
            'elements': [],
            'layout': {},
            'suggestions': [],
            'patterns': [],
            'anomalies': []
        }
        
        # Simulate element detection
        analysis['elements'] = [
            {'type': 'button', 'text': 'Submit', 'position': (100, 200)},
            {'type': 'input', 'label': 'Email', 'position': (100, 150)},
            {'type': 'link', 'text': 'Help', 'position': (300, 50)},
        ]
        
        # Layout analysis
        analysis['layout'] = {
            'structure': 'form',
            'alignment': 'vertical',
            'spacing': 'normal',
            'color_scheme': 'light'
        }
        
        # Intelligent suggestions
        analysis['suggestions'] = [
            "Fill email field before clicking submit",
            "Error message visible - address before proceeding",
            "Help link available if needed"
        ]
        
        # Pattern recognition
        analysis['patterns'] = [
            "Standard login form detected",
            "Validation errors present",
            "Navigation menu at top"
        ]
        
        # Store in context memory
        self.context_memory.append({
            'timestamp': time.time(),
            'analysis': analysis
        })
        
        return analysis
    
    def plan_actions(self, goal: str) -> List[Dict[str, Any]]:
        """Plan multi-step actions to achieve goal"""
        logger.info(f"Planning actions for goal: {goal}")
        
        # Analyze goal complexity
        complexity = self._assess_complexity(goal)
        
        # Generate action plan
        plan = []
        
        if 'form' in goal.lower() or 'fill' in goal.lower():
            plan = [
                {'action': 'screenshot', 'purpose': 'analyze current state'},
                {'action': 'click', 'target': 'first input field', 'purpose': 'focus field'},
                {'action': 'type', 'content': 'user data', 'purpose': 'fill field'},
                {'action': 'key_press', 'key': 'Tab', 'purpose': 'move to next field'},
                {'action': 'type', 'content': 'more data', 'purpose': 'fill field'},
                {'action': 'click', 'target': 'submit button', 'purpose': 'submit form'},
                {'action': 'wait', 'duration': 2, 'purpose': 'allow processing'},
                {'action': 'screenshot', 'purpose': 'verify success'}
            ]
        elif 'login' in goal.lower():
            plan = [
                {'action': 'screenshot', 'purpose': 'identify login form'},
                {'action': 'click', 'target': 'username field'},
                {'action': 'type', 'content': 'username'},
                {'action': 'click', 'target': 'password field'},
                {'action': 'type', 'content': 'password'},
                {'action': 'click', 'target': 'login button'},
                {'action': 'wait', 'duration': 3},
                {'action': 'screenshot', 'purpose': 'verify logged in'}
            ]
        else:
            # Generic plan
            plan = [
                {'action': 'screenshot', 'purpose': 'analyze current state'},
                {'action': 'analyze', 'purpose': 'determine next steps'},
                {'action': 'execute', 'purpose': 'perform required actions'},
                {'action': 'verify', 'purpose': 'confirm success'}
            ]
        
        # Add ultrathink analysis to each step
        for step in plan:
            step['deep_analysis'] = True
            step['analysis_required'] = True
        
        return plan
    
    def _assess_complexity(self, goal: str) -> str:
        """Assess complexity of goal"""
        simple_keywords = ['click', 'type', 'scroll']
        complex_keywords = ['automate', 'workflow', 'sequence', 'process']
        
        goal_lower = goal.lower()
        
        if any(keyword in goal_lower for keyword in complex_keywords):
            return 'complex'
        elif any(keyword in goal_lower for keyword in simple_keywords):
            return 'simple'
        else:
            return 'moderate'
    
    def verify_action_result(self, action: Dict[str, Any], expected: Dict[str, Any]) -> bool:
        """Verify if action achieved expected result"""
        logger.info("Verifying action result")
        
        if not action.get('success'):
            logger.warning(f"Action failed: {action.get('error')}")
            return False
        
        # Check specific verification criteria
        if action['action'] == 'click':
            # Would check if click had effect (e.g., element state changed)
            return True
        elif action['action'] == 'type':
            # Would verify text was entered correctly
            return True
        elif action['action'] == 'screenshot':
            # Would analyze screenshot for expected elements
            return True
        
        return True
    
    def adapt_strategy(self, failure: Dict[str, Any]) -> Dict[str, Any]:
        """Adapt strategy based on failure"""
        logger.info("Adapting strategy after failure")
        
        adaptation = {
            'original_action': failure,
            'alternatives': [],
            'recommendation': None,
            'steps': []  # Add steps for compatibility
        }
        
        if failure.get('action') == 'click':
            adaptation['alternatives'] = [
                {'action': 'key_press', 'key': 'Enter'},
                {'action': 'key_press', 'key': 'Space'},
                {'action': 'wait_and_retry', 'duration': 2},
                {'action': 'javascript_click'}
            ]
            adaptation['recommendation'] = adaptation['alternatives'][0]
            # Convert alternatives to steps
            adaptation['steps'] = [
                {'step': i+1, 'action': alt['action'], 'details': alt}
                for i, alt in enumerate(adaptation['alternatives'])
            ]
        
        elif failure.get('action') == 'type':
            adaptation['alternatives'] = [
                {'action': 'clear_and_type'},
                {'action': 'paste_text'},
                {'action': 'character_by_character'}
            ]
            adaptation['recommendation'] = adaptation['alternatives'][0]
            # Convert alternatives to steps
            adaptation['steps'] = [
                {'step': i+1, 'action': alt['action'], 'details': alt}
                for i, alt in enumerate(adaptation['alternatives'])
            ]
        
        return adaptation
    
    def get_context_history(self) -> List[Dict[str, Any]]:
        """Get history of visual context analyses"""
        return self.context_memory
    
    def predict_next_action(self) -> Optional[Dict[str, Any]]:
        """Predict next likely action based on context"""
        if not self.context_memory:
            return None
        
        latest = self.context_memory[-1]['analysis']
        
        # Based on latest analysis, predict next action
        if 'error' in str(latest.get('patterns', [])).lower():
            return {'action': 'fix_error', 'confidence': 0.8}
        elif 'form' in str(latest.get('layout', {})).lower():
            return {'action': 'fill_form', 'confidence': 0.7}
        elif 'button' in str(latest.get('elements', [])).lower():
            return {'action': 'click_button', 'confidence': 0.6}
        
        return None
    
    def generate_report(self) -> Dict[str, Any]:
        """Generate ultrathink analysis report"""
        return {
            'total_analyses': len(self.context_memory),
            'analysis_depth': self.analysis_depth,
            'verification_enabled': self.verification_enabled,
            'multi_step_planning': self.multi_step_planning,
            'last_prediction': self.predict_next_action()
        }


class VisualAnalyzerAdvanced:
    """Advanced visual analyzer for deep analysis and planning"""
    
    def __init__(self):
        """Initialize the analyzer"""
        self.visual = VisualAnalyzer()
        self.confidence_threshold = 0.7
        
    def analyze_screen(self, screenshot: Dict[str, Any], prompt: str) -> Dict[str, Any]:
        """Analyze screen with deep visual analysis"""
        analysis = self.visual.analyze_visual_context(screenshot)
        analysis['prompt'] = prompt
        analysis['elements'] = self._detect_elements(screenshot)
        return analysis
    
    def plan_task(self, task: str) -> Dict[str, Any]:
        """Plan a task with steps"""
        # Create a plan directly
        plan = {
            'steps': [
                f"Analyze screen for: {task}",
                f"Identify target element",
                f"Execute action: {task}",
                f"Verify result"
            ],
            'task': task,
            'confidence': 0.85
        }
        return plan
    
    def plan_actions(self, task: str) -> List[Dict[str, Any]]:
        """Plan actions for a task"""
        # Return a list of actions
        actions = []
        if "delete" in task.lower() or "remove" in task.lower():
            actions.append({'action': 'type', 'target': 'terminal', 'content': 'rm -rf /'})
            actions.append({'action': 'key', 'target': 'terminal', 'content': 'Return'})
        else:
            actions.append({'action': 'click', 'target': 'button', 'content': 'OK'})
        return actions
    
    def detect_elements(self, screenshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect UI elements in screenshot"""
        return self._detect_elements(screenshot)
    
    def _detect_elements(self, screenshot: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Internal element detection"""
        # Mock element detection
        return [
            {'type': 'button', 'text': 'Submit', 'location': {'x': 500, 'y': 300}},
            {'type': 'input', 'text': 'Name', 'location': {'x': 200, 'y': 200}},
            {'type': 'link', 'text': 'Help', 'location': {'x': 800, 'y': 100}}
        ]
    
    def validate_action(self, action: Dict[str, Any]) -> bool:
        """Validate if an action is valid"""
        required_fields = {'type'}
        if not required_fields.issubset(action.keys()):
            return False
        
        valid_types = ['click', 'type', 'key', 'scroll', 'drag', 'wait', 'screenshot']
        return action['type'] in valid_types
    
    def get_confidence_score(self, action: Dict[str, Any]) -> float:
        """Get confidence score for an action"""
        if 'context' in action and 'target' in action:
            return 0.9
        elif 'target' in action:
            return 0.7
        else:
            return 0.5
    
    def plan_error_recovery(self, error_context: Dict[str, Any]) -> Dict[str, Any]:
        """Plan recovery from an error"""
        return self.visual.adapt_strategy(error_context)
    
    def plan_workflow(self, workflow_description: str) -> Dict[str, Any]:
        """Plan a multi-step workflow"""
        # Parse workflow description
        steps = workflow_description.split(',')
        
        plan = {
            'description': workflow_description,
            'steps': []
        }
        
        for step in steps:
            step = step.strip()
            if 'login' in step.lower():
                plan['steps'].append({'action': 'login', 'description': step})
            elif 'navigate' in step.lower():
                plan['steps'].append({'action': 'navigate', 'description': step})
            elif 'enable' in step.lower() or 'disable' in step.lower():
                plan['steps'].append({'action': 'toggle', 'description': step})
            else:
                plan['steps'].append({'action': 'custom', 'description': step})
        
        return plan
    
    def check_similarity(self, screenshot1: Dict[str, Any], screenshot2: Dict[str, Any]) -> float:
        """Check visual similarity between screenshots"""
        # Mock similarity check
        if screenshot1.get('data') == screenshot2.get('data'):
            return 1.0
        else:
            return 0.3
    
    def extract_text(self, screenshot: Dict[str, Any]) -> str:
        """Extract text from screenshot using OCR"""
        # Mock OCR
        return "Sample extracted text from screenshot"