import sys
import io
import contextlib

class CodeInterpreter:
    def __init__(self):
        pass

    def execute_code(self, code):
        """Python code ko run karke output return karta hai"""
        output = io.StringIO()
        try:
            with contextlib.redirect_stdout(output):
                # Code execute ho raha hai
                exec(code)
            result = output.getvalue()
            return result if result else "✅ Code executed successfully (No output)."
        except Exception as e:
            return f"❌ Error: {str(e)}"

interpreter = CodeInterpreter()
