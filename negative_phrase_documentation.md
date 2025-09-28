# Negative Phrase Endpoint Documentation

## Overview
The `/negative-phrase` endpoint generates a list of negative keywords for Amazon PPC campaigns. These keywords help prevent wasted ad spend by excluding irrelevant searches that might trigger your ads but attract the wrong customers.

## Endpoint Details

### URL
```
POST /negative-phrase
```

### Request Format

#### Headers
```
Content-Type: application/json
```

#### Request Body
```json
{
  "asin": "B018DQI53G",
  "country": "US"  // Optional, defaults to "US"
}
```

#### Parameters
- `asin` (string, required): The Amazon Standard Identification Number of the product
- `country` (string, optional): The Amazon marketplace country code. Defaults to "US"

### Response Format

#### Success Response (200 OK)
Returns a JSON array of negative keyword strings:

```json
[
  "women",
  "womens",
  "kids",
  "cotton",
  "merino",
  "heated",
  "electric",
  "top only",
  "bottom only",
  "compression",
  "carhartt",
  "under armour",
  "lightweight",
  "summer"
]
```

#### Error Responses

**400 Bad Request**
- Missing or invalid ASIN
- JSON parsing error from AI model

```json
{
  "detail": "Failed to parse JSON array from model response: [error details]"
}
```

**503 Service Unavailable**
- Keepa API unavailable or rate limited
- Unable to fetch product details

```json
{
  "detail": "Failed to fetch product details from Keepa: [error details]"
}
```

**500 Internal Server Error**
- OpenRouter API failure
- Missing API keys

```json
{
  "detail": "OpenRouter request failed with status [status]: [error details]"
}
```

## Implementation Examples

### JavaScript (Fetch API)
```javascript
async function getNegativePhrases(asin) {
  const response = await fetch('http://localhost:8000/negative-phrase', {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
    },
    body: JSON.stringify({
      asin: asin,
      country: 'US'
    })
  });

  if (!response.ok) {
    const error = await response.json();
    throw new Error(error.detail);
  }

  const negativePhrases = await response.json();
  return negativePhrases;
}

// Usage
try {
  const phrases = await getNegativePhrases('B018DQI53G');
  console.log('Negative phrases:', phrases);
} catch (error) {
  console.error('Error:', error);
}
```

### React Component Example
```jsx
import React, { useState, useEffect } from 'react';

function NegativePhrases({ asin }) {
  const [phrases, setPhrases] = useState([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState(null);

  useEffect(() => {
    if (!asin) return;

    const fetchNegativePhrases = async () => {
      setLoading(true);
      setError(null);

      try {
        const response = await fetch('/api/negative-phrase', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
          },
          body: JSON.stringify({ asin })
        });

        if (!response.ok) {
          const errorData = await response.json();
          throw new Error(errorData.detail || 'Failed to fetch negative phrases');
        }

        const data = await response.json();
        setPhrases(data);
      } catch (err) {
        setError(err.message);
      } finally {
        setLoading(false);
      }
    };

    fetchNegativePhrases();
  }, [asin]);

  if (loading) return <div>Loading negative phrases...</div>;
  if (error) return <div>Error: {error}</div>;

  return (
    <div>
      <h3>Negative Keywords ({phrases.length})</h3>
      <div className="phrase-grid">
        {phrases.map((phrase, index) => (
          <span key={index} className="phrase-tag">
            {phrase}
          </span>
        ))}
      </div>
    </div>
  );
}
```

### Axios Example
```javascript
import axios from 'axios';

const getNegativePhrases = async (asin, country = 'US') => {
  try {
    const response = await axios.post('/negative-phrase', {
      asin,
      country
    });
    return response.data;
  } catch (error) {
    if (error.response) {
      // Server responded with error
      console.error('Error:', error.response.data.detail);
      throw new Error(error.response.data.detail);
    } else if (error.request) {
      // No response received
      console.error('No response from server');
      throw new Error('Server not responding');
    } else {
      // Request setup error
      console.error('Error:', error.message);
      throw error;
    }
  }
};
```

## Response Time Expectations
- Typical response time: 3-5 seconds
- Factors affecting response time:
  - Keepa API response time for fetching product details
  - OpenRouter AI model processing time
  - Product complexity and category

## Rate Limiting
The endpoint is subject to rate limiting based on:
- Keepa API limits (varies by subscription)
- OpenRouter API limits (varies by model and subscription)

## Best Practices

### Frontend Implementation
1. **Show loading state**: Response can take 3-5 seconds
2. **Handle errors gracefully**: Display user-friendly error messages
3. **Cache responses**: Consider caching results for the same ASIN to reduce API calls
4. **Batch display**: For better UX, display phrases in a grid or chip format
5. **Export functionality**: Allow users to copy/export the list for use in Amazon Ads

### Error Handling
```javascript
const errorMessages = {
  503: 'Product details unavailable. Please try again later.',
  400: 'Invalid product ID or temporary processing error.',
  500: 'Server error. Please contact support if the issue persists.',
  default: 'An unexpected error occurred. Please try again.'
};

function getErrorMessage(statusCode) {
  return errorMessages[statusCode] || errorMessages.default;
}
```

### UI Suggestions
1. **Copy to Clipboard**: Add a button to copy all phrases
2. **Download CSV**: Export phrases as CSV for bulk upload to Amazon
3. **Phrase Count**: Display total count prominently
4. **Category Groups**: Optionally group phrases by type (colors, sizes, materials, etc.)
5. **Selection Interface**: Allow users to select/deselect phrases before export

## Testing the Endpoint

### cURL Test
```bash
curl -X POST "http://localhost:8000/negative-phrase" \
  -H "Content-Type: application/json" \
  -d '{"asin": "B018DQI53G"}' \
  -s | jq '.'
```

### Postman Configuration
1. Method: POST
2. URL: `http://localhost:8000/negative-phrase`
3. Headers: `Content-Type: application/json`
4. Body (raw JSON):
```json
{
  "asin": "B018DQI53G",
  "country": "US"
}
```

## Model Information
- **AI Model**: Claude Sonnet 4 (via OpenRouter)
- **Purpose**: Generates contextually relevant negative keywords based on product details
- **Approach**: Focuses on high-probability search terms that would actually be used by customers but should be excluded from campaigns

## Support
For issues or questions about the negative phrase endpoint, please check:
- API logs for detailed error messages
- Keepa API status for product data availability
- OpenRouter API status for AI model availability