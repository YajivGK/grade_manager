import React from 'react';
import '../styles/SearchBar.css';

const SearchBar = ({ value, onChange, placeholder = "Search by name or reg no..." }) => {
  return (
    <div className="search-bar">
      <input
        type="text"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder={placeholder}
        className="search-input"
      />
    </div>
  );
};

export default SearchBar;

