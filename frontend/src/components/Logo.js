import React from 'react';

const Logo = ({ size = 40, color = '#3498db' }) => {
  return (
    <svg width={size} height={size} viewBox="0 0 100 100" fill="none" xmlns="http://www.w3.org/2000/svg">
      <path d="M50 10C33.4315 10 20 23.4315 20 40C20 56.5685 33.4315 70 50 70C66.5685 70 80 56.5685 80 40C80 23.4315 66.5685 10 50 10Z" fill={color} />
      <path d="M35 35C35 32.2386 37.2386 30 40 30C42.7614 30 45 32.2386 45 35C45 37.7614 42.7614 40 40 40C37.2386 40 35 37.7614 35 35Z" fill="white" />
      <path d="M55 35C55 32.2386 57.2386 30 60 30C62.7614 30 65 32.2386 65 35C65 37.7614 62.7614 40 60 40C57.2386 40 55 37.7614 55 35Z" fill="white" />
      <path d="M30 55C30 55 35 65 50 65C65 65 70 55 70 55" stroke="white" strokeWidth="3" strokeLinecap="round" />
      <path d="M25 85C25 85 35 75 50 75C65 75 75 85 75 85" stroke={color} strokeWidth="3" strokeLinecap="round" />
      <path d="M20 75C20 75 30 90 50 90C70 90 80 75 80 75" stroke={color} strokeWidth="3" strokeLinecap="round" />
    </svg>
  );
};

export default Logo;