import { useEffect, useRef, useState } from 'react'

interface Location {
  lat: number
  lon: number
  label: string
}

interface Props {
  label: string
  placeholder: string
  value: string
  onSelect: (location: Location) => void
  disabled?: boolean
}

export default function LocationPicker({
  label,
  placeholder,
  value,
  onSelect,
  disabled = false,
}: Props) {
  const [input, setInput] = useState(value)
  const [suggestions, setSuggestions] = useState<Location[]>([])
  const [open, setOpen] = useState(false)
  const [loading, setLoading] = useState(false)
  const [error, setError] = useState<string | null>(null)
  const timerRef = useRef<ReturnType<typeof setTimeout>>(
    undefined as unknown as ReturnType<typeof setTimeout>,
  )
  const selectedLabelRef = useRef(value)
  const requestIdRef = useRef(0)
  const inputRef = useRef<HTMLInputElement>(null)
  const containerRef = useRef<HTMLDivElement>(null)

  useEffect(() => {
    setInput(value)
    selectedLabelRef.current = value
  }, [value])

  // Debounced geocode search
  useEffect(() => {
    clearTimeout(timerRef.current)
    const requestId = ++requestIdRef.current
    if (!input.trim()) {
      setSuggestions([])
      setOpen(false)
      setError(null)
      return
    }
    if (input === selectedLabelRef.current) {
      setSuggestions([])
      setOpen(false)
      setLoading(false)
      setError(null)
      return
    }

    setLoading(true)
    setError(null)
    timerRef.current = setTimeout(async () => {
      try {
        // Call the backend /api/geocode endpoint (we'll add this)
        const res = await fetch(
          `/api/geocode/?query=${encodeURIComponent(input)}`,
        )
        if (!res.ok) throw new Error('Geocoding failed')
        const data = await res.json()
        if (requestId !== requestIdRef.current) return
        const results = data.results || []
        setSuggestions(results)
        setOpen(results.length > 0)
      } catch (err: unknown) {
        if (requestId !== requestIdRef.current) return
        setError(err instanceof Error ? err.message : 'Search failed')
        setSuggestions([])
      } finally {
        if (requestId === requestIdRef.current) setLoading(false)
      }
    }, 300)
  }, [input])

  // Close dropdown when clicking outside
  useEffect(() => {
    function handleClickOutside(e: MouseEvent) {
      if (
        containerRef.current &&
        !containerRef.current.contains(e.target as Node)
      ) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClickOutside)
    return () => document.removeEventListener('mousedown', handleClickOutside)
  }, [])

  function handleSelect(loc: Location) {
    requestIdRef.current += 1
    selectedLabelRef.current = loc.label
    setInput(loc.label)
    setSuggestions([])
    setOpen(false)
    onSelect(loc)
  }

  return (
    <div className="location-picker" ref={containerRef}>
      <label htmlFor={`location-${label}`}>{label}</label>
      <div className="location-picker__input-wrapper">
        <input
          ref={inputRef}
          id={`location-${label}`}
          type="text"
          value={input}
          onChange={(e) => {
            selectedLabelRef.current = ''
            setInput(e.target.value)
          }}
          onFocus={() => {
            if (suggestions.length > 0 && input !== selectedLabelRef.current) {
              setOpen(true)
            }
          }}
          placeholder={placeholder}
          disabled={disabled}
          autoComplete="off"
        />
        {loading && <span className="location-picker__spinner">…</span>}
      </div>
      {error && <div className="location-picker__error">{error}</div>}
      {open && suggestions.length > 0 && (
        <ul className="location-picker__dropdown">
          {suggestions.map((loc, i) => (
            <li key={i}>
              <button
                type="button"
                onClick={() => handleSelect(loc)}
                className="location-picker__suggestion"
              >
                {loc.label}
              </button>
            </li>
          ))}
        </ul>
      )}
    </div>
  )
}
