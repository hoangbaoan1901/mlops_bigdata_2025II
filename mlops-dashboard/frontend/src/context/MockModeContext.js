import React, { createContext, useState, useContext } from 'react';

const MockModeContext = createContext();

export const useMockMode = () => useContext(MockModeContext);

const MockModeProvider = ({ children }) => {
  // Đặt giá trị mặc định là false để sử dụng dữ liệu thực tế
  const [mockMode, setMockMode] = useState(false);

  const toggleMockMode = () => {
    setMockMode(prevMode => !prevMode);
  };

  return (
    <MockModeContext.Provider value={{ mockMode, setMockMode, toggleMockMode }}>
      {children}
    </MockModeContext.Provider>
  );
};

export default MockModeProvider; 