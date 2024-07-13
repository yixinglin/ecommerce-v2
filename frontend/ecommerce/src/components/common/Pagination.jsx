import index from 'country-flag-emoji';
import React from 'react';

function Pagination({ currentPage, totalPages, onPageChange }) {
  const pages = [];

  for (let i = 1; i <= totalPages; i++) {
    pages.push(i);
  }

  return (
    <div>
      {pages.map((page, index) => (
        index === 0 || index === pages.length - 1 || (index >= currentPage - 2 && index <= currentPage + 2) ? (
        <button 
          // className={page === currentPage? 'active' : ''}
          style={{ backgroundColor: page === currentPage? '#007bff' : '' }}
          key={page}
          onClick={() => onPageChange(page)}
        >
          {page}
        </button>        
        ) : null
      ))}
    </div>
  );
}

export default Pagination;
