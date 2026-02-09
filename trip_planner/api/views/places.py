"""
Places Autocomplete API proxy.
"""
import requests
from django.conf import settings
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status


class PlacesAutocompleteView(APIView):
    """Proxy for Google Places Autocomplete API."""
    
    def get(self, request):
        query = request.query_params.get('q', '')
        if not query or len(query) < 2:
            return Response({'predictions': []})
        
        api_key = settings.GOOGLE_PLACES_API_KEY
        if not api_key:
            # Return stub data for demo
            return Response({
                'predictions': [
                    {'description': f'{query}, USA', 'place_id': 'stub1'},
                    {'description': f'{query} City, Japan', 'place_id': 'stub2'},
                    {'description': f'{query} Beach, Australia', 'place_id': 'stub3'},
                ]
            })
        
        try:
            resp = requests.get(
                'https://maps.googleapis.com/maps/api/place/autocomplete/json',
                params={
                    'input': query,
                    'types': '(cities)',
                    'key': api_key,
                },
                timeout=10
            )
            resp.raise_for_status()
            data = resp.json()
            
            predictions = [
                {
                    'description': p.get('description'),
                    'place_id': p.get('place_id'),
                }
                for p in data.get('predictions', [])[:5]
            ]
            
            return Response({'predictions': predictions})
            
        except Exception as e:
            return Response(
                {'error': str(e)},
                status=status.HTTP_502_BAD_GATEWAY
            )
