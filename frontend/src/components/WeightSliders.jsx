import { useState } from 'react'

const aspects = [
  { key: 'food_quality', label: 'Food Quality', icon: '🍽️' },
  { key: 'service', label: 'Service', icon: '👥' },
  { key: 'ambiance', label: 'Ambiance', icon: '🎵' },
  { key: 'value', label: 'Value/Price', icon: '💰' },
  { key: 'cleanliness', label: 'Cleanliness', icon: '✨' },
  { key: 'location', label: 'Location', icon: '📍' }
]

export default function WeightSliders({ weights, onChange }) {
  return (
    <div className="space-y-4">
      {aspects.map(aspect => (
        <div key={aspect.key} className="space-y-2">
          <div className="flex items-center justify-between">
            <label className="text-sm font-medium text-gray-700 flex items-center gap-2">
              <span>{aspect.icon}</span>
              <span>{aspect.label}</span>
            </label>
            <span className="text-sm text-gray-500">
              {(weights[aspect.key] * 100).toFixed(0)}%
            </span>
          </div>
          <input
            type="range"
            min="0"
            max="100"
            value={weights[aspect.key] * 100}
            onChange={(e) => onChange(aspect.key, parseFloat(e.target.value) / 100)}
            className="w-full h-2 bg-gray-200 rounded-lg appearance-none cursor-pointer accent-blue-600"
          />
        </div>
      ))}
    </div>
  )
}
