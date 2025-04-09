import React, { useState, useEffect } from 'react';
import { InputTextarea } from 'primereact/inputtextarea';
import { InputNumber } from 'primereact/inputnumber';
import { Button } from 'primereact/button';
import { RadioButton } from 'primereact/radiobutton';
import { createBlindResults, updateEvaluation } from '../api/evaluationApi';
import { NavLink } from 'react-router-dom';
import { ProgressSpinner } from 'primereact/progressspinner';
 
function BlindResultsPage() {
 
  const [fullName, setFullName] = useState('');
 
  useEffect(() => {
    const storedName = localStorage.getItem('fullName');
    if (storedName) {
      setFullName(storedName);
    }
  }, []);
 
  const [userQuery, setUserQuery] = useState(() => {
    return localStorage.getItem('OptimizedOutput') || '';
  });
 
 
  const [numVersions, setnumVersions] = useState(2);
 
  const [blindResults, setBlindResults] = useState([]);
 
  const [revealModelNames, setRevealModelNames] = useState(false);
 
  const [response, setResponse] = useState(null);
 
  const [selectedIndex, setSelectedIndex] = useState(null);
 
  const [errorMsg, setErrorMsg] = useState('');
    const [errornumberMsg, setErrornumberMsg] = useState('');
  const [loading, setLoading] = useState(false);

  async function handleGenerate() {
    setErrorMsg('');
    setErrornumberMsg('')
    setBlindResults([]);
    setSelectedIndex(null);
    setRevealModelNames(false);
 
    if (!userQuery.trim()) {
      setErrorMsg('Please enter (or load) some text.');
      return;
    }
    if (numVersions >4 || numVersions < 2) {
        setErrornumberMsg('Please set the number from 3 to 5')
        return;
      }
    try {
      setLoading(true);
      const payload = {
        user_query: userQuery,
        num_versions: numVersions
      };
      const responseData = await createBlindResults(payload);
 
      setResponse(responseData);
 
      localStorage.setItem('responseId', responseData._id);
 
      if (!responseData.blind_results) {
        throw new Error('No "blind_results" found in response');
      }
      console.log('Response data >> ', responseData)
      setBlindResults(responseData.blind_results);
    } catch (err) {
      console.error(err);
      setErrorMsg(err.message);
    } finally {
      setLoading(false);
    }
  }
 
 
  async function handleSelectedModel(index) {
    setSelectedIndex(index);
 
    const chosenModel = blindResults[index].model;
 
    try {
        if (!response?.id) {
            throw new Error('No response data found or missing ID.');
        }
 
        await updateEvaluation(response.id, {
            chosen_model_after_blind_results: chosenModel
        });
 
    } catch (error) {
        console.error(error);
        alert(error.message);
    }
 
    setRevealModelNames(true);
  }
 
  return (
    <div className="p-4">
            <div className="columns-wrapper">
            <div className="form-container  container_border" style={{ 
              paddingRight: '200px',
              justifyContent: 'start'
              }}>
            <div className="flex justify-content-end login">
              <span style= {{
                
              }} >Hello, {fullName}</span>
          </div>
          </div>

          <div className="user-query">
            <div className="menu">
          <li>
            <NavLink
              to="/optimize"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Optimization Page
            </NavLink>
          </li>
          <li>
            <NavLink
              to="/evaluate"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Evaluation Page
            </NavLink>
          </li>

          <li>
            <NavLink
              to="/compare"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Compare Page
            </NavLink>
          </li>
        </div>

    
    <div className="blind-container">
      <h2>Blind Results Page</h2>
 
      {/* Optional instructions / error messages */}
      {errorMsg && (
        <div className="my-2 p-error" style={{ color: 'red' }}>
          {errorMsg}
        </div>
      )}
 
      {/* 1) Input text area */}
      <div className="field mb-3">
        <InputTextarea
          value={userQuery}
          onChange={(e) => setUserQuery(e.target.value)}
          rows={4}
          cols={60}
          placeholder="Enter or edit your text here..."
          className="w-full"
        />
      </div>
 
      {/* 2) Number of versions: default=2, max=4 */}
      {errornumberMsg && (
        <div className="my-2 p-error" style={{ color: 'red' }}>
          {errornumberMsg}
        </div>
        )}
      <div className="field mb-3 versions_pos" >
        <label className="block mb-2" style={{ fontWeight: 'bold' }}>
          Number of Versions
        </label>
        <InputNumber
          value={numVersions}
          onValueChange={(e) => setnumVersions(e.value)}
          className="custom-input-number"
          style={{ width: '20px' }}
        />
      </div>
 
      {/* Button: Generate Blind Results */}
      <Button
        onClick={handleGenerate}
        className="mt-2" style={{ MarginTop: '15px' }}
        >
        {loading ? (
        <span style={{ display: 'flex', alignItems: 'center' }}>
            <ProgressSpinner style={{width: '20px', height: '20px'}} strokeWidth="4" fill="var(--surface-ground)" animationDuration=".5s" />
            <span style={{ marginLeft: '0.5rem' }}>Generating...</span>
        </span>
        ) : (
        "Generate Blind Results"
        )}
        </Button>
 
      {/* If we have blindResults, show them */}
      {blindResults.length > 0 && (
        <div className="mt-4 elements_gap">
          <h3>Blind Results (pick one)</h3>
          {blindResults.map((item, idx) => (
            <div
              key={idx}
              className="mb-3 p-2"
              style={{ border: '1px solid #ccc', borderRadius: '4px' }}
            >
              <div className="flex align-items-start mb-2">
                {/* Radio button to select this version */}
                <RadioButton
                  inputId={`version-${idx}`}
                  name="selectedVersion"
                  value={idx}
                  onChange={() => handleSelectedModel(idx)}
                  checked={selectedIndex === idx}
                  disabled={selectedIndex !== null && selectedIndex !== idx}
                />
                <label htmlFor={`version-${idx}`} className="ml-2">
                  Version #{idx + 1}
                </label>
              </div>
 
              {/* Only show the response text */}
              <InputTextarea
                value={item.response || ''}
                rows={4}
                cols={60}
                readOnly
                className="w-full"
              />
 
              {/* If revealModelNames == true, show the model as well */}
              {revealModelNames && (
                <div className="mt-2">
                  <b>Model:</b> {item.model}
                </div>
              )}
            </div>
          ))}
        </div>
      )}
    </div>
    </div>
    </div>
    </div>
  );
}
 
export default BlindResultsPage;