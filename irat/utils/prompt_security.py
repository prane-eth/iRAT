# Author: Alvaro Arteaga
# This helper utility is to protect the entire project from malicious user prompts or poisoned data.
from last_layer.core import scan_prompt, Threat


def is_safe(prompt: str) -> bool:
	risk = scan_prompt(prompt)        
	if risk.has(Threat.InvisibleUnicodeDetector):
		return False
	if risk.has(Threat.HiddenTextDetector):
		return False
	if risk.has(Threat.Base64Detector):
		return False
	if risk.has(Threat.ExploitClassifier):
		return False
	if risk.has(Threat.ObfuscationDetector):
		return False
	return True

class UnsafePromptError(Exception):
	"""Custom exception for unsafe prompts."""
	def __init__(self, prompt: str):
		super().__init__(f"Unsafe prompt detected: {prompt}")
		self.prompt = prompt

	def __str__(self):
		return f"UnsafePromptError: {self.prompt}"
