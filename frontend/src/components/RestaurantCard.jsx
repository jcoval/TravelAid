import { useState } from 'react'

export default function RestaurantCard({ restaurant }) {
  const [expanded, setExpanded] = useState(false)

  const {
    name,
    address,
    adjusted_rating,
    confidence_interval,
    bias_detected,
    review_count,
    source_ratings
  } = restaurant

  const confidenceLower = (adjusted_rating - confidence_interval).toFixed(2)
  const confidenceUpper = (adjusted_rating + confidence_interval).toFixed(2)

  return (
    <div className="bg-white rounded-lg shadow hover:shadow-md transition-shadow p-6">
      <div className="flex items-start justify-between">
        <div className="flex-1">
          <h3 className="text-lg font-semibold text-gray-900">{name}</h3>
          <p className="text-sm text-gray-600 mt-1">{address}</p>
        </div>
        <div className="ml-4 text-right">
          <div className="text-2xl font-bold text-blue-600">
            {adjusted_rating.toFixed(2)}
          </div>
          <div className="text-xs text-gray-500">
            ± {confidence_interval.toFixed(2)}
          </div>
        </div>
      </div>

      <div className="mt-4 flex items-center gap-4 text-sm">
        <div className="flex items-center gap-1">
          <span className="text-gray-600">Range:</span>
          <span className="font-medium text-gray-900">
            {confidenceLower} - {confidenceUpper}
          </span>
        </div>
        <div className="flex items-center gap-1">
          <span className="text-gray-600">Reviews:</span>
          <span className="font-medium text-gray-900">{review_count}</span>
        </div>
        {bias_detected && (
          <div className="flex items-center gap-1 text-amber-600">
            <span>⚠️</span>
            <span className="font-medium">Possible bias detected</span>
          </div>
        )}
      </div>

      {source_ratings && (
        <div className="mt-4">
          <button
            onClick={() => setExpanded(!expanded)}
            className="text-sm text-blue-600 hover:text-blue-700 font-medium"
          >
            {expanded ? '▼ Hide' : '▶ Show'} source breakdown
          </button>

          {expanded && (
            <div className="mt-3 pt-3 border-t border-gray-200 grid grid-cols-3 gap-4">
              {source_ratings.google !== undefined && (
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">Google</div>
                  <div className="text-sm font-semibold text-gray-900">
                    {source_ratings.google.toFixed(1)}
                  </div>
                </div>
              )}
              {source_ratings.yelp !== undefined && (
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">Yelp</div>
                  <div className="text-sm font-semibold text-gray-900">
                    {source_ratings.yelp.toFixed(1)}
                  </div>
                </div>
              )}
              {source_ratings.tripadvisor !== undefined && (
                <div className="text-center">
                  <div className="text-xs text-gray-600 mb-1">TripAdvisor</div>
                  <div className="text-sm font-semibold text-gray-900">
                    {source_ratings.tripadvisor.toFixed(1)}
                  </div>
                </div>
              )}
            </div>
          )}
        </div>
      )}
    </div>
  )
}
