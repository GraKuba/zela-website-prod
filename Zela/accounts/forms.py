from django import forms
from .models import Location


class LocationForm(forms.ModelForm):
    """Form for creating and editing user locations."""
    
    class Meta:
        model = Location
        fields = ['name', 'address_line_1', 'address_line_2', 'city', 'province', 
                  'postal_code', 'country', 'is_main']
        widgets = {
            'name': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'e.g., Home, Office'
            }),
            'address_line_1': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Street address'
            }),
            'address_line_2': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Apartment, suite, etc. (optional)'
            }),
            'city': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'City'
            }),
            'province': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Province/State'
            }),
            'postal_code': forms.TextInput(attrs={
                'class': 'form-input',
                'placeholder': 'Postal code'
            }),
            'country': forms.Select(attrs={
                'class': 'form-select'
            }),
            'is_main': forms.CheckboxInput(attrs={
                'class': 'form-checkbox'
            })
        }
        labels = {
            'is_main': 'Set as main location',
            'address_line_2': 'Address Line 2 (optional)',
            'postal_code': 'Postal Code (optional)'
        }
    
    def __init__(self, *args, **kwargs):
        self.user = kwargs.pop('user', None)
        super().__init__(*args, **kwargs)
        
        # Country choices - Angola as default
        self.fields['country'].choices = [
            ('AO', 'Angola'),
            ('BR', 'Brazil'),
            ('PT', 'Portugal'),
            ('US', 'United States'),
            ('GB', 'United Kingdom'),
        ]