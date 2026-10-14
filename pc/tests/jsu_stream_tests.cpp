#include <cassert>
#include <cstring>
#include "JSystem/JSupport/JSURandomInputStream.h"

class MemoryStream final : public JSURandomInputStream {
    const char bytes[3] = {'a', 'b', 'c'};
    int position = 0;
public:
    int getLength() const override { return sizeof(bytes); }
    int getPosition() const override { return position; }
    int readData(void *buffer, s32 size) override {
        const int available = getLength() - position;
        const int count = size < available ? size : available;
        if (count <= 0)
            return 0;
        std::memcpy(buffer, bytes + position, count);
        position += count;
        return count;
    }
    int seekPos(s32 offset, JSUStreamSeekFrom from) override {
        const int base = from == JSU_SEEK_SET ? 0 : from == JSU_SEEK_CUR ? position : getLength();
        const int next = base + offset;
        if (next < 0 || next > getLength())
            return 0;
        const int delta = next - position;
        position = next;
        return delta;
    }
};

int main() {
    MemoryStream stream;
    char buffer[4] = {};
    assert(stream.read(buffer, sizeof(buffer)) == 3);
    assert(std::memcmp(buffer, "abc", 3) == 0);
    /* libc's EOF macro is -1; the stream state must contain only its EOF bit. */
    assert(stream.mState == JSU_EOF);
    stream.mState |= 4;
    stream.seek(0, JSU_SEEK_SET);
    assert(stream.mState == 4);
    stream.mState = GOOD;
    assert(stream.peek(buffer, 2) == 2);
    assert(stream.getPosition() == 0);
    assert(stream.isGood());
    stream.skip(1);
    assert(stream.getPosition() == 1);
    assert(stream.read(buffer, 1) == 1 && buffer[0] == 'b');
}
