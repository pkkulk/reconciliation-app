import React, { useState, useRef } from 'react';
import axios from 'axios';
import { Upload, FileSpreadsheet, FileCheck, AlertCircle, Loader2 } from 'lucide-react';
import { motion, AnimatePresence } from 'framer-motion';
import clsx from 'clsx';
export default function UploadForm({ onUploadSuccess, onUploadStart, isProcessing }) {
    const [files, setFiles] = useState({ statement: null, settlement: null });
    const [error, setError] = useState('');
    const [dragActive, setDragActive] = useState({ statement: false, settlement: false });
    const handleFileChange = (type, file) => {
        if (file && (file.name.endsWith('.xlsx') || file.name.endsWith('.xls'))) {
            setFiles(prev => ({ ...prev, [type]: file }));
            setError('');
        } else {
            setError('Please upload valid Excel files (.xlsx, .xls)');
        }
    };
    const handleDrop = (e, type) => {
        e.preventDefault();
        e.stopPropagation();
        setDragActive(prev => ({ ...prev, [type]: false }));
        if (e.dataTransfer.files && e.dataTransfer.files[0]) {
            handleFileChange(type, e.dataTransfer.files[0]);
        }
    };
    const handleDrag = (e, type, isActive) => {
        e.preventDefault();
        e.stopPropagation();
        if (e.type === "dragenter" || e.type === "dragover") {
            setDragActive(prev => ({ ...prev, [type]: true }));
        } else if (e.type === "dragleave") {
            setDragActive(prev => ({ ...prev, [type]: false }));
        }
    };
    const handleSubmit = async (e) => {
        e.preventDefault();
        setError('');
        if (!files.statement || !files.settlement) {
            setError("Please select both Statement and Settlement files.");
            return;
        }
        onUploadStart();
        const formData = new FormData();
        formData.append('statement_file', files.statement);
        formData.append('settlement_file', files.settlement);
        try {
            const response = await axios.post('http://localhost:8000/reconcile', formData, {
                headers: { 'Content-Type': 'multipart/form-data' },
            });
            onUploadSuccess(response.data);
        } catch (err) {
            console.error(err);
            setError(err.response?.data?.detail || "An error occurred during reconciliation. Please check your files.");
        }
    };
    const FileInput = ({ type, label, file }) => (
        <div
            className={clsx(
                "relative group cursor-pointer transition-all duration-300 rounded-xl border-2 border-dashed p-8 flex flex-col items-center justify-center text-center space-y-4",
                dragActive[type] ? "border-indigo-500 bg-indigo-50/50 scale-[1.02]" : "border-slate-300 bg-white hover:border-indigo-400 hover:bg-slate-50",
                file ? "border-emerald-500 bg-emerald-50/30" : ""
            )}
            onDragEnter={(e) => handleDrag(e, type, true)}
            onDragLeave={(e) => handleDrag(e, type, false)}
            onDragOver={(e) => handleDrag(e, type, true)}
            onDrop={(e) => handleDrop(e, type)}
        >
            <input
                type="file"
                accept=".xlsx,.xls"
                onChange={(e) => handleFileChange(type, e.target.files[0])}
                className="absolute inset-0 w-full h-full opacity-0 cursor-pointer z-10"
            />
            <div className={clsx("p-4 rounded-full transition-colors", file ? "bg-emerald-100 text-emerald-600" : "bg-indigo-50 text-indigo-600 group-hover:bg-indigo-100")}>
                {file ? <FileCheck className="w-8 h-8" /> : <FileSpreadsheet className="w-8 h-8" />}
            </div>
            <div>
                <h3 className="font-semibold text-slate-900">{label}</h3>
                <p className="text-sm text-slate-500 mt-1 max-w-[200px] truncate">
                    {file ? file.name : "Drag & drop or Click to Browse"}
                </p>
            </div>
            {file && (
                <motion.div
                    initial={{ scale: 0 }} animate={{ scale: 1 }}
                    className="absolute top-3 right-3 text-emerald-500"
                >
                    <FileCheck className="w-5 h-5" />
                </motion.div>
            )}
        </div>
    );
    return (
        <motion.div
            layout
            className="bg-white/80 backdrop-blur-xl shadow-2xl rounded-3xl p-8 border border-white/20 max-w-4xl mx-auto"
        >
            <form onSubmit={handleSubmit} className="space-y-8">
                <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
                    <FileInput type="statement" label="Statement File" file={files.statement} />
                    <FileInput type="settlement" label="Settlement File" file={files.settlement} />
                </div>
                <AnimatePresence>
                    {error && (
                        <motion.div
                            initial={{ opacity: 0, height: 0 }}
                            animate={{ opacity: 1, height: 'auto' }}
                            exit={{ opacity: 0, height: 0 }}
                            className="flex items-center space-x-2 text-rose-600 bg-rose-50 p-4 rounded-lg text-sm font-medium"
                        >
                            <AlertCircle className="w-5 h-5 flex-shrink-0" />
                            <span>{error}</span>
                        </motion.div>
                    )}
                </AnimatePresence>
                <div className="flex justify-center pt-2">
                    <button
                        type="submit"
                        disabled={isProcessing || !files.statement || !files.settlement}
                        className={clsx(
                            "relative overflow-hidden w-full md:w-auto md:min-w-[240px] flex items-center justify-center space-x-2 py-4 px-8 rounded-xl font-bold text-white shadow-lg shadow-indigo-200 transition-all duration-300",
                            isProcessing || !files.statement || !files.settlement
                                ? "bg-slate-300 cursor-not-allowed text-slate-500 shadow-none"
                                : "bg-gradient-to-r from-indigo-600 to-violet-600 hover:shadow-indigo-300 hover:scale-[1.02] active:scale-95"
                        )}
                    >
                        {isProcessing ? (
                            <>
                                <Loader2 className="w-5 h-5 animate-spin" />
                                <span>Processing Reconciliation...</span>
                            </>
                        ) : (
                            <>
                                <Upload className="w-5 h-5" />
                                <span>Run Reconciliation</span>
                            </>
                        )}
                    </button>
                </div>
            </form>
        </motion.div>
    );
}
