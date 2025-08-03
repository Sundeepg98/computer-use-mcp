#!/usr/bin/env python3
"""
Advanced automation examples for computer-use-mcp
Demonstrates complex multi-step workflows with ultrathink planning
"""

import sys
import os
import json
import time
import logging

# Add parent src to path
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'src'))

from computer_use_core import ComputerUseCore
from visual_analyzer import VisualAnalyzerAdvanced
from safety_checks import SafetyChecker

# Setup logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedAutomation:
    """Advanced automation workflows with ultrathink enhancement"""
    
    def __init__(self, test_mode=True):
        self.core = ComputerUseCore(test_mode=test_mode)
        self.analyzer = VisualAnalyzerAdvanced()
        self.safety = SafetyChecker()
        self.test_mode = test_mode
        
    def web_form_automation(self):
        """Automate filling out a web form"""
        print("\n🌐 Web Form Automation")
        print("-" * 50)
        
        workflow = {
            "name": "Fill Web Form",
            "steps": [
                {
                    "action": "screenshot",
                    "params": {"analyze": "Find the form on the page"}
                },
                {
                    "action": "click",
                    "params": {"element": "Name input field"}
                },
                {
                    "action": "type",
                    "params": {"text": "John Doe"}
                },
                {
                    "action": "key",
                    "params": {"key": "Tab"}
                },
                {
                    "action": "type",
                    "params": {"text": "john.doe@example.com"}
                },
                {
                    "action": "click",
                    "params": {"element": "Submit button"}
                },
                {
                    "action": "wait",
                    "params": {"seconds": 2}
                },
                {
                    "action": "screenshot",
                    "params": {"analyze": "Verify form submission success"}
                }
            ]
        }
        
        return self._execute_workflow(workflow)
    
    def document_editing_automation(self):
        """Automate document editing tasks"""
        print("\n📝 Document Editing Automation")
        print("-" * 50)
        
        workflow = {
            "name": "Edit Document",
            "steps": [
                {
                    "action": "key",
                    "params": {"key": "Ctrl+A"}  # Select all
                },
                {
                    "action": "key",
                    "params": {"key": "Ctrl+C"}  # Copy
                },
                {
                    "action": "key",
                    "params": {"key": "Ctrl+N"}  # New document
                },
                {
                    "action": "wait",
                    "params": {"seconds": 1}
                },
                {
                    "action": "key",
                    "params": {"key": "Ctrl+V"}  # Paste
                },
                {
                    "action": "type",
                    "params": {"text": "\n\n--- Edited with Computer Use MCP ---"}
                },
                {
                    "action": "key",
                    "params": {"key": "Ctrl+S"}  # Save
                }
            ]
        }
        
        return self._execute_workflow(workflow)
    
    def window_management_automation(self):
        """Automate window arrangement and management"""
        print("\n🪟 Window Management Automation")
        print("-" * 50)
        
        workflow = {
            "name": "Arrange Windows",
            "steps": [
                {
                    "action": "screenshot",
                    "params": {"analyze": "Identify all open windows"}
                },
                {
                    "action": "key",
                    "params": {"key": "Win+Left"}  # Snap to left
                },
                {
                    "action": "wait",
                    "params": {"seconds": 0.5}
                },
                {
                    "action": "key",
                    "params": {"key": "Alt+Tab"}  # Switch window
                },
                {
                    "action": "wait",
                    "params": {"seconds": 0.5}
                },
                {
                    "action": "key",
                    "params": {"key": "Win+Right"}  # Snap to right
                },
                {
                    "action": "screenshot",
                    "params": {"analyze": "Verify windows are side by side"}
                }
            ]
        }
        
        return self._execute_workflow(workflow)
    
    def data_extraction_automation(self):
        """Automate data extraction from screen"""
        print("\n📊 Data Extraction Automation")
        print("-" * 50)
        
        # Take screenshot and analyze
        screenshot = self.core.screenshot(
            analyze="Extract all text and numbers from the screen"
        )
        
        # Process with ultrathink
        analysis = self.analyzer.analyze_screen(
            screenshot,
            "Identify tables, lists, and data fields"
        )
        
        print(f"Extracted data elements: {len(analysis.get('elements', []))}")
        
        # Simulate data extraction workflow
        workflow = {
            "name": "Extract Data",
            "steps": [
                {
                    "action": "screenshot",
                    "params": {"analyze": "Find data table"}
                },
                {
                    "action": "drag",
                    "params": {
                        "start": {"x": 100, "y": 200},
                        "end": {"x": 800, "y": 600}
                    },
                    "description": "Select table area"
                },
                {
                    "action": "key",
                    "params": {"key": "Ctrl+C"},
                    "description": "Copy selected data"
                }
            ]
        }
        
        return self._execute_workflow(workflow)
    
    def intelligent_navigation(self):
        """Navigate UI intelligently using visual analysis"""
        print("\n🧭 Intelligent Navigation")
        print("-" * 50)
        
        # Analyze current screen
        screenshot = self.core.screenshot()
        
        # Plan navigation with ultrathink
        navigation_task = "Navigate to settings and enable dark mode"
        plan = self.analyzer.plan_task(navigation_task)
        
        print(f"Navigation plan for: {navigation_task}")
        for i, step in enumerate(plan.get('steps', []), 1):
            print(f"  {i}. {step}")
        
        # Convert plan to workflow
        workflow = {
            "name": "Intelligent Navigation",
            "steps": []
        }
        
        # Add dynamic steps based on analysis
        for step in plan.get('steps', []):
            if 'click' in step.lower():
                workflow['steps'].append({
                    "action": "click",
                    "params": {"element": step}
                })
            elif 'type' in step.lower():
                workflow['steps'].append({
                    "action": "type",
                    "params": {"text": "settings"}
                })
            elif 'scroll' in step.lower():
                workflow['steps'].append({
                    "action": "scroll",
                    "params": {"direction": "down", "amount": 3}
                })
        
        return self._execute_workflow(workflow)
    
    def batch_file_operations(self):
        """Automate batch file operations"""
        print("\n📁 Batch File Operations")
        print("-" * 50)
        
        workflow = {
            "name": "Batch File Operations",
            "steps": [
                {
                    "action": "key",
                    "params": {"key": "Win+E"},
                    "description": "Open file explorer"
                },
                {
                    "action": "wait",
                    "params": {"seconds": 1}
                },
                {
                    "action": "key",
                    "params": {"key": "Ctrl+A"},
                    "description": "Select all files"
                },
                {
                    "action": "key",
                    "params": {"key": "F2"},
                    "description": "Rename mode"
                },
                {
                    "action": "type",
                    "params": {"text": "batch_renamed_"}
                },
                {
                    "action": "key",
                    "params": {"key": "Enter"}
                }
            ]
        }
        
        return self._execute_workflow(workflow)
    
    def error_recovery_automation(self):
        """Demonstrate error recovery in automation"""
        print("\n🔧 Error Recovery Automation")
        print("-" * 50)
        
        workflow = {
            "name": "Error Recovery Demo",
            "steps": [
                {
                    "action": "click",
                    "params": {"x": 99999, "y": 99999},  # Invalid coordinates
                    "fallback": {
                        "action": "screenshot",
                        "params": {"analyze": "Find clickable area"}
                    }
                },
                {
                    "action": "type",
                    "params": {"text": "Test with recovery"}
                },
                {
                    "action": "verify",
                    "params": {"condition": "Text was typed successfully"}
                }
            ]
        }
        
        results = []
        for step in workflow['steps']:
            try:
                result = self._execute_step(step)
                results.append({"step": step, "result": result, "status": "success"})
            except Exception as e:
                logger.warning(f"Step failed: {e}")
                if 'fallback' in step:
                    logger.info("Executing fallback action")
                    fallback_result = self._execute_step(step['fallback'])
                    results.append({
                        "step": step,
                        "result": fallback_result,
                        "status": "recovered"
                    })
                else:
                    results.append({
                        "step": step,
                        "error": str(e),
                        "status": "failed"
                    })
        
        return results
    
    def _execute_workflow(self, workflow):
        """Execute a workflow with all steps"""
        print(f"\nExecuting workflow: {workflow['name']}")
        print(f"Steps: {len(workflow['steps'])}")
        
        results = []
        for i, step in enumerate(workflow['steps'], 1):
            description = step.get('description', step['action'])
            print(f"  Step {i}: {description}")
            
            if self.test_mode:
                # In test mode, simulate execution
                result = {
                    "action": step['action'],
                    "params": step.get('params', {}),
                    "status": "simulated",
                    "test_mode": True
                }
            else:
                result = self._execute_step(step)
            
            results.append(result)
            
            # Small delay between steps
            time.sleep(0.5)
        
        print(f"✅ Workflow completed: {len(results)} steps executed")
        return results
    
    def _execute_step(self, step):
        """Execute a single automation step"""
        action = step['action']
        params = step.get('params', {})
        
        if action == 'screenshot':
            return self.core.screenshot(**params)
        elif action == 'click':
            if 'element' in params:
                # Use visual analysis to find element
                screenshot = self.core.screenshot(
                    analyze=f"Find {params['element']}"
                )
                # Extract coordinates from analysis
                # This would be more sophisticated in production
                return {"clicked": params['element'], "method": "visual"}
            else:
                return self.core.click(
                    params.get('x', 0),
                    params.get('y', 0),
                    params.get('button', 'left')
                )
        elif action == 'type':
            text = params.get('text', '')
            if self.safety.check_text_safety(text):
                return self.core.type_text(text)
            else:
                raise ValueError(f"Unsafe text blocked: {text}")
        elif action == 'key':
            return self.core.key_press(params.get('key', 'Enter'))
        elif action == 'scroll':
            return self.core.scroll(
                params.get('direction', 'down'),
                params.get('amount', 3)
            )
        elif action == 'drag':
            start = params.get('start', {})
            end = params.get('end', {})
            return self.core.drag(
                start.get('x', 0),
                start.get('y', 0),
                end.get('x', 100),
                end.get('y', 100)
            )
        elif action == 'wait':
            time.sleep(params.get('seconds', 1))
            return {"waited": params.get('seconds', 1)}
        elif action == 'verify':
            # Verification step - would check condition
            return {"verified": params.get('condition', 'unknown')}
        else:
            raise ValueError(f"Unknown action: {action}")

def main():
    """Run advanced automation examples"""
    print("=" * 70)
    print("Computer Use MCP - Advanced Automation Examples")
    print("=" * 70)
    
    # Create automation instance (test mode by default)
    automation = AdvancedAutomation(test_mode=True)
    
    examples = [
        ("Web Form Automation", automation.web_form_automation),
        ("Document Editing", automation.document_editing_automation),
        ("Window Management", automation.window_management_automation),
        ("Data Extraction", automation.data_extraction_automation),
        ("Intelligent Navigation", automation.intelligent_navigation),
        ("Batch File Operations", automation.batch_file_operations),
        ("Error Recovery", automation.error_recovery_automation),
    ]
    
    print("\n⚠️  Running in TEST MODE - no actual actions performed")
    print("To run with real actions: AdvancedAutomation(test_mode=False)\n")
    
    for name, func in examples:
        try:
            print(f"\n{'='*70}")
            result = func()
            print(f"\n✅ {name} completed successfully")
            time.sleep(1)  # Pause between examples
        except Exception as e:
            print(f"\n❌ {name} failed: {e}")
    
    print("\n" + "=" * 70)
    print("🎉 Advanced automation examples completed!")
    print("=" * 70)

if __name__ == "__main__":
    main()