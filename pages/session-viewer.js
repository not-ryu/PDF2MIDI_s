import { useEffect, useState } from 'react';
import { useRouter } from 'next/router';
import Image from 'next/image';

export default function SessionViewer() {
    const router = useRouter();
    const { sessionId } = router.query;
    const [images, setImages] = useState(null);

    useEffect(() => {
        if (sessionId) {
            fetch(`/api/session-images?sessionId=${sessionId}`)
                .then(res => res.json())
                .then(data => setImages(data))
                .catch(err => console.error('Failed to fetch images:', err));
        }
    }, [sessionId]);

    if (!images) return <div>Loading...</div>;

    return (
        <div className="container mx-auto p-8">
            <h1 className="text-2xl font-bold mb-6">Session Images</h1>

            {Object.entries(images).map(([category, imageList]) => (
                <div key={category} className="mb-8">
                    <h2 className="text-xl font-semibold mb-4 capitalize">{category} Images</h2>
                    <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                        {imageList.map((image, index) => (
                            <div key={index} className="border rounded-lg overflow-hidden">
                                <Image
                                    src={`/api/images/${sessionId}/${category}/${image}`}
                                    alt={`${category} image ${index + 1}`}
                                    width={400}
                                    height={300}
                                    className="w-full"
                                />
                            </div>
                        ))}
                    </div>
                </div>
            ))}
        </div>
    );
} 