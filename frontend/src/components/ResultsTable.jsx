import React, { useState, useMemo } from 'react';
import { ChevronLeft, ChevronRight, Search, Download } from 'lucide-react';
import { motion } from 'framer-motion';
export default function ResultsTable({ data, title, type }) {
    const [currentPage, setCurrentPage] = useState(1);
    const [searchQuery, setSearchQuery] = useState('');
    const rowsPerPage = 10;
    const filteredData = useMemo(() => {
        if (!data) return [];
        if (!searchQuery) return data;
        const lowerQuery = searchQuery.toLowerCase();
        return data.filter(row =>
            Object.values(row).some(val =>
                String(val).toLowerCase().includes(lowerQuery)
            )
        );
    }, [data, searchQuery]);
    const totalPages = Math.ceil(filteredData.length / rowsPerPage);
    const currentData = filteredData.slice(
        (currentPage - 1) * rowsPerPage,
        currentPage * rowsPerPage
    );
    const handlePageChange = (newPage) => {
        if (newPage >= 1 && newPage <= totalPages) {
            setCurrentPage(newPage);
        }
    };
    if (!data || data.length === 0) {
        return (
            <div className="bg-white p-12 text-center rounded-b-2xl">
                <div className="bg-slate-50 rounded-full w-16 h-16 flex items-center justify-center mx-auto mb-4">
                    <Search className="w-8 h-8 text-slate-300" />
                </div>
                <h3 className="text-lg font-bold text-slate-800">No records found</h3>
                <p className="text-slate-500 mt-2">There are no transactions in the {title} category.</p>
            </div>
        );
    }
    const headers = Object.keys(data[0]).filter(k => k !== '_merge' && k !== 'VarianceVal');
    const formatCell = (key, value) => {
        if (value === null || value === undefined) return <span className="text-slate-300">-</span>;
        if (key.includes('USD') || key.includes('Amt')) {
            const num = parseFloat(value);
            if (!isNaN(num)) {
                return new Intl.NumberFormat('en-US', { style: 'currency', currency: 'USD' }).format(num);
            }
        }
        return String(value);
    };
    return (
        <div className="bg-white">
            {}
            <div className="px-6 py-4 border-b border-slate-200 flex flex-col sm:flex-row sm:items-center justify-between gap-4">
                <div className="relative max-w-sm w-full">
                    <div className="absolute inset-y-0 left-0 pl-3 flex items-center pointer-events-none">
                        <Search className="h-4 w-4 text-slate-400" />
                    </div>
                    <input
                        type="text"
                        placeholder="Search transaction..."
                        className="block w-full pl-10 pr-3 py-2 border border-slate-300 rounded-lg leading-5 bg-slate-50 placeholder-slate-400 focus:outline-none focus:bg-white focus:ring-2 focus:ring-indigo-500 focus:border-indigo-500 sm:text-sm transition duration-150 ease-in-out"
                        value={searchQuery}
                        onChange={(e) => { setSearchQuery(e.target.value); setCurrentPage(1); }}
                    />
                </div>
                <div className="text-sm text-slate-500 font-medium">
                    Showing {filteredData.length} records
                </div>
            </div>
            {}
            <div className="overflow-x-auto min-h-[400px]">
                <table className="min-w-full divide-y divide-slate-200">
                    <thead className="bg-slate-50">
                        <tr>
                            {headers.map((h) => (
                                <th key={h} className="px-6 py-3 text-left text-xs font-semibold text-slate-500 uppercase tracking-wider whitespace-nowrap">
                                    {h.replace(/_/g, ' ')}
                                </th>
                            ))}
                        </tr>
                    </thead>
                    <tbody className="bg-white divide-y divide-slate-100">
                        {currentData.map((row, i) => (
                            <motion.tr
                                initial={{ opacity: 0 }}
                                animate={{ opacity: 1 }}
                                transition={{ delay: i * 0.05 }}
                                key={i}
                                className="hover:bg-slate-50/80 transition-colors"
                            >
                                {headers.map((h) => (
                                    <td key={h} className="px-6 py-4 whitespace-nowrap text-sm text-slate-600 font-medium">
                                        {formatCell(h, row[h])}
                                    </td>
                                ))}
                            </motion.tr>
                        ))}
                    </tbody>
                </table>
                {currentData.length === 0 && (
                    <div className="p-8 text-center text-slate-500">
                        No search results found.
                    </div>
                )}
            </div>
            {}
            {totalPages > 1 && (
                <div className="px-6 py-4 border-t border-slate-200 bg-slate-50 rounded-b-2xl flex items-center justify-between">
                    <div className="text-sm text-slate-500">
                        Page {currentPage} of {totalPages}
                    </div>
                    <div className="flex space-x-2">
                        <button
                            onClick={() => handlePageChange(currentPage - 1)}
                            disabled={currentPage === 1}
                            className="p-2 rounded-lg border border-slate-300 bg-white text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <ChevronLeft className="w-4 h-4" />
                        </button>
                        <div className="flex items-center px-4 font-medium text-slate-700">
                            {currentPage}
                        </div>
                        <button
                            onClick={() => handlePageChange(currentPage + 1)}
                            disabled={currentPage === totalPages}
                            className="p-2 rounded-lg border border-slate-300 bg-white text-slate-500 hover:bg-slate-50 disabled:opacity-50 disabled:cursor-not-allowed"
                        >
                            <ChevronRight className="w-4 h-4" />
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}
