import React, { useState } from 'react';
import { motion, AnimatePresence } from 'framer-motion';
import { Upload, LayoutDashboard, FileText, AlertCircle, CheckCircle, XCircle, RefreshCw } from 'lucide-react';
import UploadForm from './components/UploadForm';
import SummaryCards from './components/SummaryCards';
import ResultsTable from './components/ResultsTable';
function App() {
  const [results, setResults] = useState(null);
  const [activeTab, setActiveTab] = useState('matched');
  const [isProcessing, setIsProcessing] = useState(false);
  const handleUploadSuccess = (data) => {
    setResults(data);
    setActiveTab('matched');
    setIsProcessing(false);
  };
  const handleUploadStart = () => {
    setResults(null);
    setIsProcessing(true);
  };
  const tabs = [
    { id: 'matched', label: 'Matched', icon: CheckCircle, color: 'text-emerald-500' },
    { id: 'variance', label: 'Variance', icon: AlertCircle, color: 'text-amber-500' },
    { id: 'only_in_statement', label: 'Statement Only', icon: FileText, color: 'text-blue-500' },
    { id: 'only_in_settlement', label: 'Settlement Only', icon: FileText, color: 'text-purple-500' },
    { id: 'reversal_mismatch', label: 'Mismatch', icon: RefreshCw, color: 'text-rose-500' },
  ];
  const getActiveData = () => {
    if (!results) return [];
    return results[activeTab];
  };
  return (
    <div className="min-h-screen bg-slate-50 font-sans text-slate-900">
      {}
      <header className="bg-white shadow-sm border-b border-slate-200 sticky top-0 z-10">
        <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
          <div className="flex items-center space-x-3">
            <div className="bg-indigo-600 p-2 rounded-lg">
              <LayoutDashboard className="h-6 w-6 text-white" />
            </div>
            <h1 className="text-xl font-bold bg-clip-text text-transparent bg-gradient-to-r from-indigo-600 to-violet-600">
              Reconcile<span className="text-slate-700">Pro</span>
            </h1>
          </div>
          <div className="text-sm text-slate-500">
            v1.0.0
          </div>
        </div>
      </header>
      <main className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8 space-y-8">
        {}
        <section className="space-y-6">
          {!results && !isProcessing && (
            <div className="text-center space-y-2 mb-8 animate-fade-in-up">
              <h2 className="text-3xl font-extrabold text-slate-900 tracking-tight">
                Financial Reconciliation Made Simple
              </h2>
              <p className="text-lg text-slate-600 max-w-2xl mx-auto">
                Upload your Statement and Settlement files to instantly analyze discrepancies, variances, and matches.
              </p>
            </div>
          )}
          <div className={`transition-all duration-500 ${results ? 'scale-95 opacity-50 hover:opacity-100 hover:scale-100' : 'scale-100'}`}>
            <UploadForm onUploadSuccess={handleUploadSuccess} onUploadStart={handleUploadStart} isProcessing={isProcessing} />
          </div>
        </section>
        {}
        <AnimatePresence>
          {results && (
            <motion.div
              initial={{ opacity: 0, y: 20 }}
              animate={{ opacity: 1, y: 0 }}
              transition={{ duration: 0.5 }}
            >
              <div className="space-y-8">
                {}
                <div>
                  <h3 className="text-lg font-semibold text-slate-800 mb-4 px-1">Overview</h3>
                  <SummaryCards summary={results.summary} />
                </div>
                {}
                <div className="bg-white rounded-2xl shadow-xl overflow-hidden border border-slate-200">
                  {}
                  <div className="border-b border-slate-200 bg-slate-50/50 backdrop-blur-sm">
                    <div className="flex overflow-x-auto hide-scrollbar px-4 pt-4 whitespace-nowrap gap-2">
                      {tabs.map((tab) => {
                        const Icon = tab.icon;
                        const isActive = activeTab === tab.id;
                        return (
                          <button
                            key={tab.id}
                            onClick={() => setActiveTab(tab.id)}
                            className={`relative flex items-center space-x-2 px-4 py-3 text-sm font-medium rounded-t-lg transition-all duration-200 ${isActive
                                ? 'bg-white text-indigo-600 shadow-sm border-x border-t border-slate-200 -mb-px z-10'
                                : 'text-slate-500 hover:text-slate-700 hover:bg-slate-100/50'
                              }`}
                          >
                            <Icon className={`h-4 w-4 ${isActive ? tab.color : 'text-slate-400'}`} />
                            <span>{tab.label}</span>
                            {isActive && (
                              <motion.div
                                layoutId="activeTabIndicator"
                                className="absolute top-0 left-0 right-0 h-0.5 bg-indigo-600 rounded-t-full"
                              />
                            )}
                          </button>
                        );
                      })}
                    </div>
                  </div>
                  {}
                  <div className="p-0">
                    <ResultsTable
                      data={getActiveData()}
                      title={tabs.find(t => t.id === activeTab)?.label}
                      type={activeTab}
                    />
                  </div>
                </div>
              </div>
            </motion.div>
          )}
        </AnimatePresence>
      </main>
    </div>
  );
}
export default App;
