import { useState } from 'react'
import WeightSliders from './components/WeightSliders'
import RestaurantList from './components/RestaurantList'

function App() {
  const [weights, setWeights] = useState({
    food_quality: 1.0,
    service: 1.0,
    ambiance: 1.0,
    value: 1.0,
    cleanliness: 1.0,
    location: 1.0
  })

  const [results, setResults] = useState([])
  const [loading, setLoading] = useState(false)

  const handleWeightChange = (aspect, value) => {
    setWeights(prev => ({
      ...prev,
      [aspect]: value
    }))
  }

  const handleSearch = async () => {
    setLoading(true)
    try {
      const response = await fetch('/api/search', {
        method: 'POST',
        headers: {
          'Content-Type': 'application/json',
        },
        body: JSON.stringify({
          city: 'Boston, MA',
          weights: weights
        })
      })
      const data = await response.json()
      setResults(data.restaurants || [])
    } catch (error) {
      console.error('Error fetching results:', error)
      // For development, show mock data
      setResults([
        {
          name: "Sample Restaurant",
          address: "123 Main St, Boston, MA",
          adjusted_rating: 4.2,
          confidence_interval: 0.3,
          bias_detected: false,
          review_count: 150,
          source_ratings: {
            google: 4.3,
            yelp: 4.1,
            tripadvisor: 4.2
          }
        }
      ])
    } finally {
      setLoading(false)
    }
  }

  return (
    <div className="min-h-screen bg-gray-50">
      <header className="bg-white shadow-sm">
        <div className="max-w-7xl mx-auto px-4 py-6 sm:px-6 lg:px-8">
          <h1 className="text-3xl font-bold text-gray-900">TravelAid</h1>
          <p className="mt-1 text-sm text-gray-500">
            Meta-review aggregator for Boston restaurants
          </p>
        </div>
      </header>

      <main className="max-w-7xl mx-auto px-4 py-8 sm:px-6 lg:px-8">
        <div className="grid grid-cols-1 lg:grid-cols-3 gap-8">
          {/* Controls Section */}
          <div className="lg:col-span-1">
            <div className="bg-white rounded-lg shadow p-6">
              <h2 className="text-lg font-semibold text-gray-900 mb-4">
                Customize Weights
              </h2>
              <p className="text-sm text-gray-600 mb-4">
                Adjust what matters most to you
              </p>
              <WeightSliders
                weights={weights}
                onChange={handleWeightChange}
              />
              <button
                onClick={handleSearch}
                disabled={loading}
                className="mt-6 w-full bg-blue-600 text-white px-4 py-2 rounded-md hover:bg-blue-700 disabled:bg-gray-400 disabled:cursor-not-allowed transition-colors"
              >
                {loading ? 'Searching...' : 'Search Restaurants'}
              </button>
            </div>
          </div>

          {/* Results Section */}
          <div className="lg:col-span-2">
            <RestaurantList restaurants={results} loading={loading} />
          </div>
        </div>
      </main>
    </div>
  )
}

export default App
