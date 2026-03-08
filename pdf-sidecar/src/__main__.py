#!/usr/bin/env python3
"""PDF Sidecar - JSON-RPC Server for PDF Operations"""

import sys
import json
import logging
from typing import Any
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[logging.StreamHandler(sys.stderr)]
)
logger = logging.getLogger(__name__)


class JSONRPCServer:
    """Simple JSON-RPC 2.0 server over stdio"""
    
    def __init__(self):
        self.methods = {}
        self._register_builtin_methods()
    
    def _register_builtin_methods(self):
        """Register built-in methods"""
        self.methods['system.ping'] = self._ping
        self.methods['system.info'] = self._system_info
    
    def _ping(self, params: dict) -> dict:
        """Health check endpoint"""
        return {'status': 'ok', 'message': 'PDF Sidecar is running'}
    
    def _system_info(self, params: dict) -> dict:
        """Get system information"""
        import platform
        return {
            'python_version': platform.python_version(),
            'platform': platform.system(),
            'architecture': platform.machine()
        }
    
    def register_method(self, name: str, handler: callable):
        """Register a method handler"""
        self.methods[name] = handler
        logger.info(f"Registered method: {name}")
    
    def handle_request(self, request: dict) -> dict:
        """Process a JSON-RPC request"""
        request_id = request.get('id')
        method = request.get('method')
        params = request.get('params', {})
        
        if not method:
            return self._error_response(request_id, -32600, 'Invalid Request: method is required')
        
        if method not in self.methods:
            return self._error_response(request_id, -32601, f'Method not found: {method}')
        
        try:
            result = self.methods[method](params or {})
            return self._success_response(request_id, result)
        except Exception as e:
            logger.exception(f"Error executing {method}")
            return self._error_response(request_id, -32603, str(e))
    
    def _success_response(self, request_id: Any, result: Any) -> dict:
        """Create a success response"""
        return {
            'jsonrpc': '2.0',
            'result': result,
            'id': request_id
        }
    
    def _error_response(self, request_id: Any, code: int, message: str) -> dict:
        """Create an error response"""
        return {
            'jsonrpc': '2.0',
            'error': {
                'code': code,
                'message': message
            },
            'id': request_id
        }
    
    def run(self):
        """Main server loop - reads from stdin, writes to stdout"""
        logger.info("PDF Sidecar started, waiting for requests...")
        
        try:
            # Read binary data from stdin to avoid encoding issues on Windows
            stdin_buffer = sys.stdin.buffer if hasattr(sys.stdin, 'buffer') else sys.stdin
            
            for line_bytes in stdin_buffer:
                try:
                    # Decode as UTF-8
                    line = line_bytes.decode('utf-8').strip() if isinstance(line_bytes, bytes) else line_bytes.strip()
                    if not line:
                        continue
                    
                    logger.info(f"Raw input: {line}")
                    request = json.loads(line)
                    logger.info(f"Parsed request: {request.get('method')}")
                    
                    response = self.handle_request(request)
                    print(json.dumps(response), flush=True)
                    
                except json.JSONDecodeError as e:
                    error_response = self._error_response(None, -32700, f'Parse error: {e}')
                    print(json.dumps(error_response), flush=True)
        except KeyboardInterrupt:
            logger.info("Shutting down...")
        except Exception as e:
            logger.exception("Fatal error in server loop")
            raise


def main():
    """Entry point"""
    server = JSONRPCServer()
    
    # Import and register handlers
    from src.handlers import merge, split, convert, edit, thumbnails
    
    merge.register(server)
    split.register(server)
    convert.register(server)
    edit.register(server)
    thumbnails.register(server)
    server.run()


if __name__ == '__main__':
    main()
