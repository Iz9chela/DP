import React, { useState, useEffect } from 'react';
import { InputTextarea } from 'primereact/inputtextarea';
import { Button } from 'primereact/button';
import { Dropdown } from 'primereact/dropdown';
import { updateEvaluation, createComparison } from '../api/evaluationApi';
import { NavLink } from 'react-router-dom';
import { ProgressSpinner } from 'primereact/progressspinner';
import 'primeicons/primeicons.css';

function ComparePage() {
  const [fullName, setFullName] = useState('');
  const [isLoading, setIsLoading] = useState(false);


  const [isProviderOpen, setIsProviderOpen] = useState(false);
  
    useEffect(() => {
      const storedName = localStorage.getItem('fullName');
      if (storedName) {
        setFullName(storedName);
      }
    }, []);
  
  // -- Provider & model dynamic mapping --
  const providerOptions = [
    { label: 'OpenAI', value: 'openai' },
    { label: 'Claude', value: 'claude' }
  ];

  const modelOptionsMap = {
    openai: [
      { label: 'gpt-3.5-turbo', value: 'gpt-3.5-turbo' },
      { label: 'gpt-4o', value: 'gpt-4o' },
      { label: 'gpt-4o-mini', value: 'gpt-4o-mini' },
      { label: 'o3-mini', value: 'o3-mini' }
    ],
    claude: [
      { label: 'claude-3-haiku-20240307', value: 'claude-3-haiku-20240307' },
      { label: 'claude-3-5-haiku-latest', value: 'claude-3-5-haiku-latest' },
      { label: 'claude-3-7-sonnet-latest', value: 'claude-3-7-sonnet-latest' }
    ]
  };

  // Example states
  const [userRequest, setUserRequest] = useState('');
  const [userRequestOptimized, setUserRequestOptimized] = useState('');
  const [output1, setOutput1] = useState('');
  const [output2, setOutput2] = useState('');
  const [provider, setProvider] = useState('openai');
  const [model, setModel] = useState(modelOptionsMap['openai'][0].value);

  const [feedbackGiven, setFeedbackGiven] = useState(false);
  const [compareResult, setCompareResult] = useState('');

  // Handle provider changes
  function handleCopyDefault() {
    navigator.clipboard.writeText(output1)
      .then(() => alert("Default query copied"))
      .catch((err) => console.error("Copy failed", err));
  }
  
  function handleCopyOptimized() {
    navigator.clipboard.writeText(output2)
      .then(() => alert("Optimized query copied"))
      .catch((err) => console.error("Copy failed", err));
  }
  
  function handleProviderChange(e) {
    setProvider(e.value);
    setModel(modelOptionsMap[e.value][0].value);
  }
  const [errorMsg, setErrorMsg] = useState('');
  async function handleCompare() {
    setErrorMsg('');
 
    if (!userRequest.trim() ||!userRequestOptimized.trim() ) {
      setErrorMsg('Please enter (or load) text in the both fields.');
      return;
    }
    try {
      setIsLoading(true);
      const compareData = {
        user_query: userRequest,           
        optimized_user_query: userRequestOptimized,
        provider,
        model
      };

      const response = await createComparison(compareData);
      console.log('Compare result => ', response);
      setCompareResult(response);
      
      localStorage.setItem('compareId', response._id);
      // parse the default & optimized responses
      if (response.parsed_result_after_comparison) {
        const defResp = response.parsed_result_after_comparison.default_query_response;
        const optResp = response.parsed_result_after_comparison.optimized_query_response;

        // If they're JSON or strings, adapt as needed
        setOutput1(JSON.stringify(defResp, null, 2));
        setOutput2(JSON.stringify(optResp, null, 2));
      }
      setFeedbackGiven(false);
      
    } catch (err) {
      console.error(err);
      alert('Compare request failed: ' + err.message);
    }
      finally {
        setIsLoading(false);
      }
  }


  async function handleUserVerdict(verdict) {
      try {
        if (!compareResult?._id) {
          throw new Error('No evaluation found or missing ID.');
        }
  
        await updateEvaluation(compareResult._id, {
          user_verdict_after_comparison: verdict
        });
        
        setFeedbackGiven(true);
  
      } catch (error) {
        console.error(error);
        alert(error.message);
      }
    }

    return (
      <div className="p-4">
        <div className="columns-wrapper">
        {/* 3) Provider */}
        <div className="form-container container_border"> 
        <div className="flex justify-content-end login" style={{ marginBottom: '1rem', alignSelf: 'flex-start' }}>
          <span>Hello, {fullName}</span>
        </div>
        <div className="field mb-3" style={{ marginBottom: isProviderOpen ? '60px' : '30px' }}>
          <label className="block mb-2">AIclient</label>
          <Dropdown
            value={provider}
            options={providerOptions}
            onChange={handleProviderChange}
            className="w-full"
            appendTo="self"
            onShow={() => setIsProviderOpen(true)}
            onHide={() => setIsProviderOpen(false)}
          />
        </div>
  
        {/* 4) Model */}
        <div className="field mb-3">
          <label className="block mb-2">Model</label>
          <Dropdown
            value={model}
            options={modelOptionsMap[provider]}
            onChange={(e) => setModel(e.value)}
            placeholder="Select Model"
            className="w-full"
            appendTo="self"
          />
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
              to="/blind"
              className={({ isActive }) => (isActive ? "grey active" : "grey")}
            >
              Blind Results Page
            </NavLink>
          </li>
        </div>
        <h2>Compare Page</h2>
        {errorMsg && (
        <div className="my-2 p-error" style={{ color: 'red' }}>
          {errorMsg}
        </div>
      )}
          {/* 1) User query */}
          <div className="inputs_fields">
                <div className="field mb-3">
                <h4>Original query</h4>
          <InputTextarea
            value={userRequest}
            onChange={(e) => setUserRequest(e.target.value)}
            rows={5}
            cols={60}
            placeholder="User's original query"
            className="w-full"
          />
        </div>
  
        {/* 2) Optimized query */}
        <div className="field mb-3">
        <h4>Optimized query</h4>
          <InputTextarea
            value={userRequestOptimized}
            onChange={(e) => setUserRequestOptimized(e.target.value)}
            rows={5}
            cols={60}
            placeholder="User's improved query"
            className="w-full"
          />
        </div>
        </div>
  
        {/* Compare button */}
        <Button  
        className="p-button-info execute_pos" 
        onClick={handleCompare} 
        >
        {isLoading ? (
          <span style={{ display: 'flex', alignItems: 'center' }}>
            <ProgressSpinner style={{width: '20px', height: '20px'}} strokeWidth="4" fill="var(--surface-ground)" animationDuration=".5s" />
            <span style={{ marginLeft: '0.5rem' }}>Comparing...</span>
          </span>
        ) : (
          "Execute"
        )}
        </Button>
  
        {/* Show results side by side */}
        { (
          <div className="mt-4 p-3 border-1 border-round surface-border">
            <h2>Compare Results</h2>
  
            <div className="flex gap-3 outputs_fields" >
              <div className="flex-1">
                <div className="wrapper">
                <h4>Default Query Response</h4>
                <Button 
                  icon="pi pi-copy" 
                  className="p-button-text p-button-rounded button_size" 
                  onClick={handleCopyDefault} 
                  tooltip="Copy Default Query" 
                />
                </div>
                <InputTextarea
                  value={output1}
                  rows={8}
                  cols={50}
                  readOnly
                  className="w-full" style={{ width: '441px' }}
                />
              </div>
              <div className="flex-1">
                <div className="wrapper">
                <h4>Optimized Query Response</h4>
                <Button 
                  icon="pi pi-copy" 
                  className="p-button-text p-button-rounded button_size" 
                  onClick={handleCopyOptimized} 
                  tooltip="Copy Optimized Query" 
                />
                </div>
                <InputTextarea
                  value={output2}
                  rows={8}
                  cols={50}
                  readOnly
                  className="w-full" style={{ width: '441px' }}
                />
              </div>
            </div>
  
            {/* Feedback prompt */}
            <div className="mt-3">
              <p className="output_pos">Is the second output better?</p>
              <div className="feedback">
              <Button
                label="Worse"
                className="p-button-danger mr-2"
                disabled={feedbackGiven}
                onClick={() => handleUserVerdict('Worse')}
              />
              <Button
                label="Tie"
                className="p-button-secondary mr-2"
                disabled={feedbackGiven}
                onClick={() => handleUserVerdict('Tie')}
              />
              <Button
                label="Better"
                className="p-button-success"
                disabled={feedbackGiven}
                onClick={() => handleUserVerdict('Better')}
              />
              </div>
            </div>
          </div>
        )}
      </div>
      </div>
      </div>
    );
  }
  
  export default ComparePage;